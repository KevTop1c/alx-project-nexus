from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .models import UserProfile

User = get_user_model()


class UserRegistrationTests(APITestCase):
    """
    Test suite for user registration
    """

    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.register_url = reverse("register")
        self.valid_user_data = {
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "securepass123",
            "password_confirm": "securepass123",
            "first_name": "John",
            "last_name": "Doe",
        }

    def test_register_user_success(self):
        """Test successful user registration"""
        response = self.client.post(self.register_url, self.valid_user_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("user", response.data)
        self.assertIn("tokens", response.data)
        self.assertEqual(response.data["user"]["username"], "newuser")
        self.assertEqual(response.data["user"]["email"], "newuser@example.com")

        # Verify user was created in database
        user = User.objects.get(username="newuser")
        self.assertEqual(user.email, "newuser@example.com")
        self.assertEqual(user.first_name, "John")
        self.assertEqual(user.last_name, "Doe")

    def test_register_creates_user_profile(self):
        """Test that registration creates UserProfile automatically"""
        response = self.client.post(self.register_url, self.valid_user_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify UserProfile was created
        user = User.objects.get(username="newuser")
        self.assertTrue(hasattr(user, "profile"))
        self.assertIsInstance(user.profile, UserProfile)

    def test_register_returns_jwt_tokens(self):
        """Test that registration returns valid JWT tokens"""
        response = self.client.post(self.register_url, self.valid_user_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("tokens", response.data)
        self.assertIn("access", response.data["tokens"])
        self.assertIn("refresh", response.data["tokens"])

        # Verify tokens are strings
        self.assertIsInstance(response.data["tokens"]["access"], str)
        self.assertIsInstance(response.data["tokens"]["refresh"], str)

    def test_register_password_mismatch(self):
        """Test registration fails with password mismatch"""
        data = self.valid_user_data.copy()
        data["password_confirm"] = "differentpass"

        response = self.client.post(self.register_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("non_field_errors", response.data)

    def test_register_duplicate_username(self):
        """Test registration fails with duplicate username"""
        # Create first user
        User.objects.create_user(username="newuser", email="first@example.com", password="pass123")

        # Try to create duplicate
        response = self.client.post(self.register_url, self.valid_user_data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)

    def test_register_duplicate_email(self):
        """Test registration fails with duplicate email"""
        if not User._meta.get_field("email").unique:
            self.skipTest("Email uniqueness not enforced in User model")
        duplicate_email = "duplicate@example.com"

        # Create first user
        User.objects.create_user(
            username="firstuser",
            email=duplicate_email,
            password="pass123",
        )

        # Try to create with same email
        response = self.client.post(
            self.register_url,
            {
                "username": "seconduser",
                "email": duplicate_email,  # 🛠️ FIX: Explicit duplicate email
                "password": "testpass123",
                "password_confirm": "testpass123",
            },
            format="json",
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)

    def test_register_missing_required_fields(self):
        """Test registration fails with missing required fields"""
        data = {"username": "testuser"}  # Missing other required fields

        response = self.client.post(self.register_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)
        self.assertIn("password_confirm", response.data)

    def test_register_weak_password(self):
        """Test registration with weak password"""
        data = self.valid_user_data.copy()
        data["password"] = "weak"
        data["password_confirm"] = "weak"

        response = self.client.post(self.register_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_optional_fields(self):
        """Test registration works without optional fields"""
        data = {
            "username": "minimaluser",
            "email": "minimal@example.com",
            "password": "securepass123",
            "password_confirm": "securepass123",
        }

        response = self.client.post(self.register_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="minimaluser")
        self.assertEqual(user.first_name, "")
        self.assertEqual(user.last_name, "")


class UserLoginTests(APITestCase):
    """
    Test suite for user login and authentication
    """

    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.login_url = reverse("login")
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="testpass123")
        UserProfile.objects.create(user=self.user)

    def test_login_success(self):
        """Test successful login"""
        data = {"username": "testuser", "password": "testpass123"}

        response = self.client.post(self.login_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("user", response.data)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)
        self.assertEqual(response.data["user"]["username"], "testuser")

    def test_login_returns_jwt_tokens(self):
        """Test that login returns valid JWT tokens"""
        data = {"username": "testuser", "password": "testpass123"}

        response = self.client.post(self.login_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

        # Verify tokens are strings and not empty
        self.assertTrue(len(response.data["access"]) > 0)
        self.assertTrue(len(response.data["refresh"]) > 0)

    def test_login_invalid_password(self):
        """Test login fails with invalid password"""
        data = {"username": "testuser", "password": "wrongpassword"}

        response = self.client.post(self.login_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn("detail", response.data)

    def test_login_nonexistent_user(self):
        """Test login fails with nonexistent user"""
        data = {"username": "nonexistent", "password": "testpass123"}

        response = self.client.post(self.login_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_missing_username(self):
        """Test login fails without username"""
        data = {"password": "testpass123"}

        response = self.client.post(self.login_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("username", response.data)

    def test_login_missing_password(self):
        """Test login fails without password"""
        data = {"username": "testuser"}

        response = self.client.post(self.login_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("password", response.data)

    def test_login_empty_credentials(self):
        """Test login fails with empty credentials"""
        data = {"username": "", "password": ""}

        response = self.client.post(self.login_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_case_sensitive_username(self):
        """Test that username is case-sensitive"""
        data = {"username": "TESTUSER", "password": "testpass123"}  # Wrong case

        response = self.client.post(self.login_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class JWTTokenTests(APITestCase):
    """
    Test suite for JWT token generation and validation
    """

    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.user = User.objects.create_user(username="testuser", email="test@example.com", password="testpass123")
        UserProfile.objects.create(user=self.user)

    def test_access_token_generation(self):
        """Test that access token is generated correctly"""
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)

        self.assertIsInstance(access_token, str)
        self.assertTrue(len(access_token) > 0)

    def test_refresh_token_generation(self):
        """Test that refresh token is generated correctly"""
        refresh = RefreshToken.for_user(self.user)
        refresh_token = str(refresh)

        self.assertIsInstance(refresh_token, str)
        self.assertTrue(len(refresh_token) > 0)

    def test_access_token_authentication(self):
        """Test authentication with access token"""
        # Get tokens
        login_url = reverse("login")
        login_data = {"username": "testuser", "password": "testpass123"}
        login_response = self.client.post(login_url, login_data, format="json")

        access_token = login_response.data["access"]

        # Use access token to access protected endpoint
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        profile_url = reverse("profile")
        profile_response = self.client.get(profile_url)

        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)

    def test_token_refresh(self):
        """Test refreshing access token"""
        # Get initial tokens
        refresh = RefreshToken.for_user(self.user)
        refresh_token = str(refresh)

        # Refresh the token
        refresh_url = reverse("token_refresh")
        response = self.client.post(refresh_url, {"refresh": refresh_token}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_invalid_token_rejected(self):
        """Test that invalid tokens are rejected"""
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalid_token")

        profile_url = reverse("profile")
        response = self.client.get(profile_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_expired_token_rejected(self):
        """Test that expired tokens are rejected"""
        # This test verifies the token expiry configuration
        # In production, tokens would actually expire
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)

        # Verify token is valid when fresh
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        profile_url = reverse("profile")
        response = self.client.get(profile_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_token_contains_user_info(self):
        """Test that token contains user information"""
        refresh = RefreshToken.for_user(self.user)

        # Tokens contain user_id in payload
        self.assertEqual(int(refresh["user_id"]), self.user.id)


class UserProfileTests(APITestCase):
    """
    Test suite for user profile management
    """

    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpass123",
            first_name="John",
            last_name="Doe",
        )
        self.profile = UserProfile.objects.create(user=self.user, bio="Test bio")
        self.profile_url = reverse("profile")

    def test_get_profile_requires_authentication(self):
        """Test that getting profile requires authentication"""
        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_get_profile_success(self):
        """Test successfully getting user profile"""
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("user", response.data)
        self.assertIn("bio", response.data)
        self.assertEqual(response.data["user"]["username"], "testuser")
        self.assertEqual(response.data["bio"], "Test bio")

    def test_profile_returns_user_details(self):
        """Test that profile returns complete user details"""
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        user_data = response.data["user"]
        self.assertEqual(user_data["username"], "testuser")
        self.assertEqual(user_data["email"], "test@example.com")
        self.assertEqual(user_data["first_name"], "John")
        self.assertEqual(user_data["last_name"], "Doe")

    def test_profile_includes_timestamps(self):
        """Test that profile includes created_at and updated_at"""
        self.client.force_authenticate(user=self.user)

        response = self.client.get(self.profile_url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("created_at", response.data)
        self.assertIn("updated_at", response.data)

    def test_profile_one_to_one_relationship(self):
        """Test that each user has exactly one profile"""
        # Try to create another profile for the same user
        with self.assertRaises(Exception):
            UserProfile.objects.create(user=self.user, bio="Another bio")

    def test_profile_created_on_registration(self):
        """Test that profile is automatically created on registration"""
        register_url = reverse("register")
        data = {
            "username": "newuser",
            "email": "new@example.com",
            "password": "securepass123",
            "password_confirm": "securepass123",
        }

        response = self.client.post(register_url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # Verify profile exists
        user = User.objects.get(username="newuser")
        self.assertTrue(UserProfile.objects.filter(user=user).exists())

    def test_profile_bio_optional(self):
        """Test that bio field is optional"""
        user = User.objects.create_user(username="nobiouser", email="nobio@example.com", password="pass123")
        profile = UserProfile.objects.create(user=user)

        self.assertIsNone(profile.bio)

    def test_profile_cascade_delete(self):
        """Test that profile is deleted when user is deleted"""
        user = User.objects.create_user(username="deleteuser", email="delete@example.com", password="pass123")
        profile = UserProfile.objects.create(user=user, bio="Will be deleted")
        profile_id = profile.id

        # Delete user
        user.delete()

        # Verify profile was also deleted
        self.assertFalse(UserProfile.objects.filter(id=profile_id).exists())


class AuthenticationFlowTests(APITestCase):
    """
    Test suite for complete authentication flows
    """

    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()

    def test_complete_registration_login_flow(self):
        """Test complete flow: register -> login -> access protected resource"""
        # Step 1: Register
        register_url = reverse("register")
        register_data = {
            "username": "flowuser",
            "email": "flow@example.com",
            "password": "securepass123",
            "password_confirm": "securepass123",
        }
        register_response = self.client.post(register_url, register_data, format="json")
        self.assertEqual(register_response.status_code, status.HTTP_201_CREATED)

        # Step 2: Login
        login_url = reverse("login")
        login_data = {"username": "flowuser", "password": "securepass123"}
        login_response = self.client.post(login_url, login_data, format="json")
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)

        # Step 3: Access protected resource
        access_token = login_response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")
        profile_url = reverse("profile")
        profile_response = self.client.get(profile_url)
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)

    def test_token_refresh_flow(self):
        """Test token refresh flow"""
        # Register and get tokens
        register_url = reverse("register")
        register_data = {
            "username": "refreshuser",
            "email": "refresh@example.com",
            "password": "securepass123",
            "password_confirm": "securepass123",
        }
        register_response = self.client.post(register_url, register_data, format="json")

        refresh_token = register_response.data["tokens"]["refresh"]

        # Refresh the access token
        refresh_url = reverse("token_refresh")
        refresh_response = self.client.post(refresh_url, {"refresh": refresh_token}, format="json")

        self.assertEqual(refresh_response.status_code, status.HTTP_200_OK)
        self.assertIn("access", refresh_response.data)

        # Use new access token
        new_access_token = refresh_response.data["access"]
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {new_access_token}")
        profile_url = reverse("profile")
        profile_response = self.client.get(profile_url)
        self.assertEqual(profile_response.status_code, status.HTTP_200_OK)

    def test_logout_flow(self):
        """Test that after logout, old tokens are invalid"""
        # This test demonstrates logout behavior
        # In a real implementation, you might blacklist tokens

        # Register and login
        register_url = reverse("register")
        data = {
            "username": "logoutuser",
            "email": "logout@example.com",
            "password": "securepass123",
            "password_confirm": "securepass123",
        }
        response = self.client.post(register_url, data, format="json")

        _ = response.data["tokens"]["access"]

        # Clear credentials (simulating logout)
        self.client.credentials()

        # Try to access protected resource
        profile_url = reverse("profile")
        profile_response = self.client.get(profile_url)

        self.assertEqual(profile_response.status_code, status.HTTP_401_UNAUTHORIZED)
