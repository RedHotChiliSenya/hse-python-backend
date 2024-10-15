from datetime import datetime

from pydantic import SecretStr
import pytest
from fastapi.testclient import TestClient

from lecture_4.demo_service.api.main import create_app

from lecture_4.demo_service.core.users import UserEntity, UserRole, UserService, UserInfo, password_is_longer_than_8
from lecture_4.demo_service.api.contracts import UserResponse, RegisterUserRequest



@pytest.fixture
def user_service():
    return UserService(password_validators=[password_is_longer_than_8])

@pytest.fixture
def user_info():
    return UserInfo(
        username='imashevchenko',
        name='Arsenii',
        birthdate=datetime.fromisoformat('2002-04-22T20:30:00'),
        password=SecretStr('topsecret1')
    )

@pytest.fixture
def user_entity(user_info):
    return UserEntity(
        uid=1,
        info=user_info
    )

@pytest.fixture
def user_register_request():
    return RegisterUserRequest(
        username='imashevchenko',
        name='Arsenii',
        birthdate=datetime.fromisoformat('2002-04-22T20:30:00'),
        password=SecretStr('topsecret1')
    )


@pytest.fixture
def user_response(user_info, user_entity) -> UserResponse:
    return UserResponse(
        uid=user_entity.uid,
        username=user_info.username,
        name=user_info.name,
        birthdate=user_info.birthdate,
        role=user_info.role
    )

@pytest.fixture
def test_client():
    service = create_app()
    with TestClient(service) as client:
        yield client


@pytest.fixture
def admin_user_info() -> UserInfo:
    return UserInfo(
        username="admin",
        name="admin",
        birthdate=datetime.fromtimestamp(0.0),
        role=UserRole.ADMIN,
        password="superSecretAdminPassword123",
    )

def test_user_service(user_service, user_info, user_entity):
    entity = user_service.register(user_info)
    assert entity == user_entity

    assert user_service.get_by_username(user_info.username) == entity
    assert user_service.get_by_id(entity.uid) == entity

    user_service.grant_admin(entity.uid)
    assert user_service.get_by_id(entity.uid).info.role == UserRole.ADMIN

    with pytest.raises(ValueError):
        assert user_service.grant_admin('fake')

    assert user_service.get_by_username("fake") == None

def test_password_longer():
    assert password_is_longer_than_8('123456789')
    assert not password_is_longer_than_8('12')


def test_with_invalid_password(user_service, user_info):
    user_info.password = SecretStr('12')
    with pytest.raises(ValueError):
        user_service.register(user_info)

def test_register_already_existent(user_info, user_service):
    user_service.register(user_info)
    with pytest.raises(ValueError):
        user_service.register(user_info)    

def test_registration(test_client, user_register_request, user_response):
    response = test_client.post("/user-register", content=user_register_request.model_dump_json())

    assert response.status_code == 200

    user_response == UserResponse.model_validate(response.json())


def test_registration_invalid_password(test_client, user_register_request):
    user_register_request.password = SecretStr('sdfsdfsdf')
    response = test_client.post("/user-register", content=user_register_request.model_dump_json())

    assert response.status_code == 400

def test_get_user(test_client, user_register_request, user_response, user_entity):
    user_response.uid = 2
    register_response = test_client.post("/user-register", content=user_register_request.model_dump_json())
    auth = (user_register_request.username, user_register_request.password.get_secret_value())

    response = test_client.post("/user-get", params={'id': register_response.json()["uid"]}, auth=auth)
    
    assert response.status_code == 200
    assert user_response == UserResponse.model_validate(response.json())

    response = test_client.post("/user-get", params={}, auth=auth)
    assert response.status_code == 400

    response = test_client.post("/user-get", params={'id': user_entity.uid, 'username': user_entity.info.username}, auth=auth)
    assert response.status_code == 400
    

def test_get_user_unauthorized(test_client, user_register_request):
    user_response.uid = 2
    register_response = test_client.post("/user-register", content=user_register_request.model_dump_json())

    auth = (user_register_request.username, user_register_request.password.get_secret_value() + '435')
    response = test_client.post("/user-get", params={'id': register_response.json()["uid"]}, auth=auth)
    
    assert response.status_code == 401



def test_get_user_by_admin(test_client, admin_user_info):
    admin_auth = (admin_user_info.username, admin_user_info.password.get_secret_value())

    test_client.post("/user-register", content=admin_user_info.model_dump_json())
    response = test_client.post("/user-get", params={"username": "test"}, auth=admin_auth)
    assert response.status_code == 404

    test_client.post("/user-register", content=admin_user_info.model_dump_json())
    response = test_client.post("/user-get", params={"username": "admin"}, auth=admin_auth)
    assert response.status_code == 200


def test_promote_user_by_user(test_client, user_register_request):
    register_response = test_client.post("/user-register", content=user_register_request.model_dump_json())
    auth = (user_register_request.username, user_register_request.password.get_secret_value())

    assert register_response.status_code == 200

    promote_response = test_client.post("/user-promote", params={'id': register_response.json()["uid"]}, auth=auth)
    assert promote_response.status_code == 403

def test_promote_user_by_admin(test_client, admin_user_info):
    admin_auth = (admin_user_info.username, admin_user_info.password.get_secret_value())
    promote_response = test_client.post("/user-promote", params={'id': "1"}, auth=admin_auth)
    assert promote_response.status_code == 200