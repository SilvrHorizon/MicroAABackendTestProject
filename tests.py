import unittest

from config import TestConfig
from app import create_app, db

from app.models import User, TrainingImage

from flask import url_for

import requests
from requests.auth import HTTPBasicAuth

from PIL import Image

import base64
import io
import os

import secrets

from uuid import uuid4


TEST_IMAGE_1_PATH = os.path.abspath("TEST_IMAGE.png")

def get_file_binary(path):
    file = None
    with open(path, 'rb') as stream:
        file = stream.read()
    return file

class TestUser():
    def __init__(self, app, email, password, authenticate=True):
        super()

        self.email = email
        self.password = password

        self.client = app.test_client()
        self._create_in_api()

        if authenticate:
            self._manage_token()
        else:
            self.token = "INVALID_TOKEN"

    
    def _create_in_api(self):
        request = self.client.post('/users',
            json={'email': self.email, 'password': self.password}
        )
        self.public_id = request.json["public_id"]

        assert request.status_code == 201
    
    def _manage_token(self):
        request = self.client.get(
            '/login',
            headers={
                'Authorization': 'Basic ' + base64.b64encode(bytes(f'{self.email}:{self.password}', 'utf-8')).decode('utf-8')
            }
        )

        assert request.status_code == 200
        self.token = request.json["x-access-token"]


    def get_create_image_response(self, image_binary=None, user=None):
        if not image_binary:
            image_binary = get_file_binary(TEST_IMAGE_1_PATH)

        data = dict(image=(io.BytesIO(image_binary), 'image.png'))
        
        if user is not None:
            data['user'] = user

        return self.post('/training_images', data=data)
        

    def get_create_classified_area_response(self, training_image="", x_position=0, y_position=0, width=1, height=1, tag=None):
        return self.post(
            '/classified_areas',
            json={
                'training_image': training_image,

                'x_position': x_position,
                'y_position': y_position,

                'width': width,
                'height': height,

                'tag': tag
            }
        )

    def get(self, route=""):
        result = self.client.get(route, headers={'x-access-token': self.token})

        return result

    def post(self, route="", json=None, data=None):
        result = self.client.post(route, headers={'x-access-token': self.token},
            json=json,
            data=data)

        return result

    def put(self, route="", json=None, data=None):
        result = self.client.put(route, headers={'x-access-token': self.token},
            json=json,
            data=data)

        return result
        



class TestRoutes(unittest.TestCase):
    def response_resolves_to(self, response, status_code):
        return response.status_code == status_code

    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        self.client = self.app.test_client()
        
        self.user = TestUser(self.app, f'{secrets.token_hex(16).lower()}@helllo.com', "password")
        self.user2 = TestUser(self.app, f'{secrets.token_hex(16).lower()}@helllo.com', "password")

        self.admin = TestUser(self.app, f'{secrets.token_hex(16).lower()}@helllo.com', 'password')
        
        User.query.filter_by(public_id=self.admin.public_id).first().is_admin = True
        db.session.commit()


        self.unauthenticatedUser = TestUser(self.app, f'{secrets.token_hex(16).lower()}@helllo.com', "pass", authenticate=False)
      
    def test_authentication(self):
        # No credentials passed
        self.assertTrue(
        self.response_resolves_to(self.client.get('/secret_protected_route'), 401))

        # Invalid credentials
        self.assertTrue(
        self.response_resolves_to(self.unauthenticatedUser.get('/secret_protected_route'), 401))

        # Valid credentials
        self.assertTrue(
        self.response_resolves_to(self.user.get('/secret_protected_route'), 200))

    def test_image_upload(self):
        #Test with unauthorized user
        self.assertTrue(
        self.response_resolves_to(self.unauthenticatedUser.get_create_image_response(), 401)
        )

        # Test with invalid file
        self.assertTrue(
        self.response_resolves_to(self.user.get_create_image_response(
            get_file_binary('tests.py')
        ), 400))

        # Make sure the user cannot upload an image to another user
        self.assertTrue(
        self.response_resolves_to(self.user.get_create_image_response(
            user=self.user2.public_id
        ), 401))

        # Check that admins can create images that belong to other users
        self.assertTrue(
        self.response_resolves_to(
            self.admin.get_create_image_response(user=self.user2.public_id), 201
        ))

        # Test that image upload works
        self.assertTrue(
        self.response_resolves_to(
            self.user.get_create_image_response(), 201
        ))

        image_url = self.user.get_create_image_response().json['_links']['image']
        
        # Check that the file uploaded got saved propperly
        self.assertEqual(
            self.user.get(image_url).data,
            get_file_binary('TEST_IMAGE.png')
        )

    def test_classified_area_upload(self):
        # Create an image
        image_public_id = self.user.get_create_image_response().json["public_id"]

        self.assertTrue(
        self.response_resolves_to(
            self.user.get_create_classified_area_response(training_image="INVALID_ID", x_position=1, y_position=1, width=1, height=1, tag="Dog"),
            400
        ))

        self.assertTrue(
        self.response_resolves_to(
            self.user.get_create_classified_area_response(training_image=image_public_id, x_position=-1, y_position=1, width=1, height=1, tag="Dog"),
            400
        ))

        self.assertTrue(
        self.response_resolves_to(
            self.user.get_create_classified_area_response(training_image=image_public_id, x_position=1, y_position=-1, width=1, height=1, tag="Dog"),
            400
        ))

        self.assertTrue(
        self.response_resolves_to(
            self.user.get_create_classified_area_response(training_image=image_public_id, x_position=1, y_position=1, width=-1, height=1, tag="Dog"),
            400
        ))

        self.assertTrue(
        self.response_resolves_to(
            self.user.get_create_classified_area_response(training_image=image_public_id, x_position=1, y_position=1, width=1, height=-1, tag="Dog"),
            400
        ))

        self.assertTrue(
        self.response_resolves_to(
            self.user.get_create_classified_area_response(training_image=image_public_id, x_position=1, y_position=1, width=200, height=1, tag="Dog"),
            400
        ))

        self.assertTrue(
        self.response_resolves_to(
            self.user.get_create_classified_area_response(training_image=image_public_id, x_position=1, y_position=1, width=1, height=200, tag="Dog"),
            400
        ))

        self.assertTrue(
        self.response_resolves_to(
            self.user.get_create_classified_area_response(training_image=True, x_position=1, y_position=1, width=1, height=200, tag="Dog"),
            400
        ))

        self.assertTrue(
        self.response_resolves_to(
            self.user.get_create_classified_area_response(training_image=image_public_id, x_position="Hello", y_position=1, width=1, height=200, tag="Dog"),
            400
        ))

        self.assertTrue(
        self.response_resolves_to(
            self.user.get_create_classified_area_response(training_image=image_public_id, x_position=1, y_position=True, width=1, height=200, tag="Dog"),
            400
        ))

        self.assertTrue(
        self.response_resolves_to(
            self.user.get_create_classified_area_response(training_image=image_public_id, x_position=1, y_position=1, width=False, height=200, tag="Dog"),
            400
        ))


        self.assertTrue(
        self.response_resolves_to(
            self.user.get_create_classified_area_response(training_image=image_public_id, x_position=1, y_position=1, width=1, height=None, tag="Dog"),
            400
        ))

        self.assertTrue(
        self.response_resolves_to(
            self.user.get_create_classified_area_response(training_image=image_public_id, x_position=1, y_position=1, width=1, height=1, tag=False),
            400
        ))

        valid_arguments = dict(
            training_image=image_public_id, x_position=1, y_position=1, width=1, height=1, tag="dog"
        )
        response = self.user.get_create_classified_area_response(**valid_arguments)
        self.assertTrue(
        self.response_resolves_to(
            response,
            201
        ))

        self.assertTrue(
        self.response_resolves_to(
            self.user.get(f'/classified_areas/{response.json["public_id"]}'),
            200
        ))

        for key in valid_arguments:
            self.assertTrue(key in response.json)

            self.assertEqual(
                valid_arguments[key], response.json[key]
            )


        WIERD_STRING = "(っ◔◡◔)っ ♥ how will the db manage? ♥".lower()
        self.assertEqual(
            self.user.get(route=f'/classified_areas/{self.user.get_create_classified_area_response(training_image=image_public_id, x_position=1, y_position=1, width=1, height=1, tag=WIERD_STRING).json["public_id"]}')
                .json['tag'], WIERD_STRING
        )


    def test_put_classified_area(self):
        image = self.user.get_create_image_response().json['public_id']

        area = self.user.get_create_classified_area_response(
            training_image=image,

            x_position=0,
            y_position=0,
            
            width=1,
            height=1,
        ).json['public_id']

        json_data = dict(
            x_position=1,
            y_position=2,
            
            width=1,
            height=1,

            tag="hello"
        )

        self.assertTrue(
            self.response_resolves_to(
                self.user2.put(f'/classified_areas/{area}',
                    json=json_data), 401
            )
        )
        
        self.assertTrue(
            self.response_resolves_to(
                self.user.put(f'/classified_areas/{area}',
                    json=json_data), 200
            )
        )

        in_db = self.client.get(f'/classified_areas/{area}').json

        for key in json_data:
            self.assertEqual(json_data[key], in_db[key])

        json_data2 = dict(
            x_position=9,
            y_position=9,
            
            width=9,
            height=9,

            tag="newtag"
        )
        
        self.assertTrue(
            self.response_resolves_to(
                self.admin.put(f'/classified_areas/{area}',
                    json=json_data2), 200
            )
        )

        in_db = self.client.get(f'/classified_areas/{area}').json

        for key in json_data2:
            self.assertEqual(json_data2[key], in_db[key])



        


    def test_put_user(self):
        

        self.assertTrue(
            self.response_resolves_to(
                self.user.put(
                    f'/users/{self.user.public_id}',
                    {
                        "email": "bad_email",
                        "password": "pass"
                    }
                ),
                400
            )
        )

        self.assertTrue(
            self.response_resolves_to(
                self.user.put(
                    f'/users/{self.user.public_id}',
                    {
                        "email": 2003,
                        "password": "pass"
                    }
                ),
                400
            )
        )

        self.assertTrue(
            self.response_resolves_to(
                self.user.put(
                    f'/users/{self.user.public_id}',
                    {
                        "email": "email@mail.com",
                        "password": True
                    }
                ),
                400
            )
        )


        passed_json = {
            "email": "RANDOMTESTTHING@test.com",
            "password": "hello"
        }

        self.assertTrue(
            self.response_resolves_to(
                self.user.put(
                    f'/users/{self.user.public_id}',
                    passed_json
                ),
                200
            )
        )

        from_db = User.query.filter_by(public_id=self.user.public_id).first()
        self.assertEqual(from_db.email, passed_json["email"])
        self.assertTrue(from_db.check_password(passed_json["password"]))


        passed_json = {
            "email": "ADMINWILLCHANGETHIS@test.com",
            "password": "and this too"
        }

        # Check that a non admin cannot change
        self.assertTrue(
            self.response_resolves_to(
                self.user2.put(
                    f'/users/{self.user.public_id}',
                    passed_json
                ),
                401
            )
        )


        self.assertTrue(
            self.response_resolves_to(
                self.admin.put(
                    f'/users/{self.user.public_id}',
                    passed_json
                ),
                200
            )
        )

        from_db = User.query.filter_by(public_id=self.user.public_id).first()
        self.assertEqual(from_db.email, passed_json["email"])
        self.assertTrue(from_db.check_password(passed_json["password"]))


    def test_promote_demote_user(self):
        # Just check incase the user some how has become an admin before the test
        self.assertEqual(
            self.client.get(f'/users/{self.user.public_id}').json["is_admin"],
            False
        )

        self.assertTrue(
            self.response_resolves_to(
                self.admin.post(f'/users/{self.user.public_id}/promote'),
                200
            )
        )

        self.assertEqual(
            self.client.get(f'/users/{self.user.public_id}').json["is_admin"],
            True
        )
        self.assertTrue(
            self.response_resolves_to(
                self.admin.post(f'/users/{self.user.public_id}/demote'),
                200
            )
        )

        self.assertEqual(
            self.client.get(f'/users/{self.user.public_id}').json["is_admin"],
            False
        )


    def remove_test_images(self):
        dir_name = os.path.join('app', 'static', 'tests', 'training_images')
        test = os.listdir(dir_name)
        for item in test:
            if item.endswith(".png"):
                os.remove(os.path.join(dir_name, item))


    def tearDown(self):
        self.remove_test_images()
        db.session.remove()
        db.drop_all()
        self.app_context.pop()



class TestDatabase(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_user(self):
        u = User(email="test@example.com", password="secure_pass")
        self.assertEqual(u.email, "test@example.com")
        self.assertTrue(u.check_password("secure_pass"))

        # db.session.add(u)

    def test_training_image(self):
        u = User(email="test@example.com", password="secure_pass")

        db.session.add(u)

        i = TrainingImage(user=u)
        db.session.add(i)

        db.session.commit()

        self.assertEqual(i.user, u)
        self.assertEqual(i.user_id, u.id)


if __name__ == '__main__':
    unittest.main()
