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


FLASK_BASE_URL = "http://127.0.0.1:5000"

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


    def get_create_image_response(self, image_binary="", user=None):
        data = dict(image=(io.BytesIO(image_binary), 'image.png'))
        
        if user is not None:
            data['user'] = user

        return self.post('/training_images', data=data)
        

    def get_create_classified_area_response(self, image="", x_position=0, y_position=0, width=0, height=0, tag=None):
        return self.post(
            '/classified_areas',
            json={
                'training_image': image,

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
        

def get_file_binary(path):
    file = None
    with open(path, 'rb') as stream:
        file = stream.read()
    return file

class TestRoutes(unittest.TestCase):
    def assertResponse(self, response, status_code):
        self.assertEqual(response.status_code, status_code)

    
        


    def setUp(self):
        self.app = create_app(TestConfig)
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()

        self.client = self.app.test_client()

        self.auth_test_route = f'{FLASK_BASE_URL}/secret_protected_route'
        self.login_route = f'{FLASK_BASE_URL}/login'
        self.users_route = f'{FLASK_BASE_URL}/users'

        self.training_images_route = f'{FLASK_BASE_URL}/training_images'
        
        # print("secret", secrets.token_urlsafe(5).lower())
        self.user = TestUser(self.app, f'{secrets.token_hex(16).lower()}@helllo.com', "password")
        self.user2 = TestUser(self.app, f'{secrets.token_hex(16).lower()}@helllo.com', "password")

        self.unauthenticatedUser = TestUser(self.app, f'{secrets.token_hex(16).lower()}@helllo.com', "pass", authenticate=False)
      
    def test_authentication(self):
        # No credentials passed

        self.assertResponse(self.client.get('/secret_protected_route'), 401)
        
        self.assertResponse(self.unauthenticatedUser.get('/secret_protected_route'), 401)

        # self.assertResponse()
        self.assertResponse(self.user.get('/secret_protected_route'), 200)

    def test_image_upload(self):
        # Test that image upload works
        self.assertResponse(self.user.get_create_image_response(
            get_file_binary('TEST_IMAGE.png')
        ), 201)

        #With unauthorized user
        self.assertResponse(self.unauthenticatedUser.get_create_image_response(
            get_file_binary('TEST_IMAGE.png')
        ), 401)

        self.assertResponse(self.user.get_create_image_response(
            get_file_binary('TEST_IMAGE.png'),
            user=self.user2.public_id
        ), 401)

        self.assertResponse(self.user.get_create_image_response(
            get_file_binary('tests.py')
        ), 400)


        image_url = self.user.get_create_image_response(get_file_binary('TEST_IMAGE.png')).json['image_url']
        


        self.assertEqual(
            self.user.get(image_url).data,
            get_file_binary('TEST_IMAGE.png')
        )


        
        '''
        post_response = self.user.post('/training_images',
            data=dict(image=(io.BytesIO(binary_image), 'image.png'))
        )
        self.assertResponse(post_response, 201)
        '''

        '''

        post_response = self.client.post('/training_images', headers={
            'x-access-token': self.test_account['token']    
        }, data=dict(image=(io.BytesIO(binary_image), 'image.png')))
        self.assertResponse(post_response, 201)
        image_public_id = post_response.json['public_id']


        # Test that unauthorized users cannot upload images with other parent users than themselves 
        post_response = self.client.post('/training_images', headers={
            'x-access-token': self.test_account['token']    
        }, data=dict(user=self.test_account_2["public_id"], image=(io.BytesIO(binary_image), 'image.png')))
        self.assertResponse(post_response, 401)
        
        post_response = self.client.post(
            '/classified_areas',
            json={
                'training_image': "INVALID_IMAGE",
                'width': 20,
                "height": 20,
                "x_position": 20,
                "y_position": 20,
                "tag": "world"
            }
        )
        self.assertResponse(post_response, 400)

        post_response = self.client.post(
            '/classified_areas',
            json={
                'training_image': image_public_id,
                'width': -1,
                "height": -1,
                "x_position": 20,
                "y_position": 20,
                "tag": "world"
            }
        )
        self.assertResponse(post_response, 400)

        post_response = self.client.post(
            '/classified_areas',
            json={
                'training_image': image_public_id,
                'width': 20,
                "height": 20,
                "x_position": 300,
                "y_position": 300,
                "tag": "world"
            }
        )
        self.assertResponse(post_response, 400)

        post_response = self.client.post(
            '/classified_areas',
            json={
                'training_image': image_public_id,
                'width': 20,
                "height": 20,
                "x_position": 300,
                "y_position": 300,
                "tag": "world"
            }
        )
        self.assertResponse(post_response, 400)

        post_response = self.client.post(
            '/classified_areas',
            json={
                'training_image': image_public_id,
                'width': 0,
                "height": 0,
                "x_position": 128,
                "y_position": 128,
                "tag": "world"
            }
        )
        self.assertResponse(post_response, 201)
        '''

    def test_classified_area_upload(self):
        image_public_id = self.user.get_create_image_response(
            get_file_binary('TEST_IMAGE.png')
        ).json["public_id"]

        self.assertResponse(
            self.user.get_create_classified_area_response(image="INVALID_ID", x_position=-1, y_position=1, width=1, height=1, tag="Dog"),
            400
        )

        self.assertResponse(
            self.user.get_create_classified_area_response(image=image_public_id, x_position=-1, y_position=1, width=1, height=1, tag="Dog"),
            400
        )

        self.assertResponse(
            self.user.get_create_classified_area_response(image=image_public_id, x_position=1, y_position=-1, width=1, height=1, tag="Dog"),
            400
        )

        self.assertResponse(
            self.user.get_create_classified_area_response(image=image_public_id, x_position=1, y_position=1, width=-1, height=1, tag="Dog"),
            400
        )

        self.assertResponse(
            self.user.get_create_classified_area_response(image=image_public_id, x_position=1, y_position=1, width=1, height=-1, tag="Dog"),
            400
        )
        self.assertResponse(
            self.user.get_create_classified_area_response(image=image_public_id, x_position=1, y_position=1, width=200, height=1, tag="Dog"),
            400
        )

        self.assertResponse(
            self.user.get_create_classified_area_response(image=image_public_id, x_position=1, y_position=1, width=1, height=200, tag="Dog"),
            400
        )

        response = self.user.get_create_classified_area_response(image=image_public_id, x_position=1, y_position=1, width=1, height=1, tag="Dog")
        self.assertResponse(
            response,
            201
        )

        print(response.json)
        self.assertResponse(
            self.user.get(f'/classified_areas/{response.json["public_id"]}'),
            200
        )

        WIERD_STRING = "(っ◔◡◔)っ ♥ how will the db manage? ♥".lower()
        self.assertEqual(
            self.user.get(route=f'/classified_areas/{self.user.get_create_classified_area_response(image=image_public_id, x_position=1, y_position=1, width=1, height=1, tag=WIERD_STRING).json["public_id"]}')
                .json['tag'], WIERD_STRING
        )

    def test_image(self):
        pass
        # print(self.client.get('/users').json)
        '''
        with self.client.open():
            print(self.client.post(self.users_route, json={
                'email': "jo@test.com",
                'password': "password"
            }).json)

            credentials = base64.b64encode(b'jo@test.com:password').decode('utf-8')
            response = self.client.get('/login', headers={
                'Authorization': 'Basic ' + credentials
            })

            headers = {"x-access-token": response.json['x-access-token']}

            file_bytes = open("TEST_IMAGE.png", 'rb')
            response = self.client.post('/training_images', headers=headers, data=dict(
                image=(io.BytesIO(file_bytes.read()), 'image.png')))
            file_bytes.close()

            

            print(self.client.post())
            print(self.client.get(self.users_route).json)
            ''' 



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
