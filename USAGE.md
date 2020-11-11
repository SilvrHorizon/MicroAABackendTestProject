

# Objects:
\* - Unmodifiable attribute

\*\* - Attribute only modifiable by admins

## user:    
    'email': string             - (has to be in an 'email format')
    *'public_id': string
    **'is_admin': boolean

    'password': string          - (Only used when objects are created, has to be more than 1 characther)

    *_links: {
        *'self': relative URL             - ( URL pointing to this object )
        *'promote': relative URL          - ( URL pointing to where you can promote this user)
        *'demote': relative URL           - ( URL pointing to where you can demote this user)
        *'training_images': relative URL  - ( URL pointing to all training images of this user) 
    }



## training_image:    
    *'public_id': string

    *'height': int
    *'width': int

    'user': string                          - ( The image owner's public_id )

    *'_links': {
        *'self', relative URL               - ( URL pointing to this object )
        *'image', relative URL              - ( URL of the acctual image)
        *'user', relative URL               - ( URL of the owner)
        *'classified_areas', relative URL   - ( URL of the classified areas that belong to this training_image )
    }
    

## classified_area
    *'public_id': string
    *'training_image': string              - (The image to which this area belongs to)

    'x_position': int
    'y_position': int

    'width': int
    'height': int

    'tag': string, null

    *'links': {
        *'self'                            - ( URL pointing to this object )
        *'training_image'                  - ( URL pointing to the training image that this area belongs to )
        *'training_image_cropped'          - ( URL that contains PNG of only this areas look ) 
    }

# Collections
All collections have the following structure:
   
    *'_links': {
        *'next_page': relative URL, null
        *'prev_page': relative URL, null
        *'self': relative URL    
    }

    *'_meta': {
        'page': int
        'per_page': int
        'total_items': int
        'total_pages': int
    }

    *items: list                - ( Contains all the objects of the current page )


# Controllers

## Login route                  - ( base_url/login )
- Uses HTTP Basic Auth. Pass email and password as credentials
- Returns: x-access-token which should be included as a HTTP header in all subsequent requests

## User                         - ( base_url/users )

### POST                        - ( POST base_url/users )
- json_data(\<user\>):
- - email: required
- - password: required
- returns: the created \<user\>

### GET                         - ( GET base_url/users )
- returns: collection of \<user\>

### PUT                         - ( PUT base_url/users/\<user.public_id\> )
- json_data(\<user\>):
- - email: optional
- - password: optional

### DELETE                      - ( DELETE base_url/users/\<user.public_id\>)
- returns: 200 if successfull, 404 if no user exists of specified id.
### 'Convenience urls'
PROMOTE                         - ( POST base_url/users/\<user.public_id\>/promote)

DEMOTE                         - ( POST base_url/users/\<user.public_id\>/demote)


## TrainingImages - (base_url/training_images)
### POST                        - ( POST base_url/training_images )
- **THIS ROUTE TAKES HTML FORM DATA NOT JSON DATA**
- form_data:
- - user: optional              - public id of the user that will be the parented
- - image: required             - Image file, PNG, JPEG among others are accepted 

### GET                         - ( GET base_url/training_images )
- PARAMS:
- - user: \<user.public_id\> - Results will only include training_images parented to the user
- RETURNS: collection of \<training_image\>

### DELETE                      - ( DELETE base_url/training_images/\<training_image.public_id\>)
- returns: 200 if successfull, 404 if no user exists of specified id.



## ClassifiedAreas              - ( base_url/classified_areas )

### POST                        - ( POST base_url/classified_areas )
- json_data(\<classified_area\> ):
- - training_image: required    - ( public id of the training_image that will be the parented )
- - x_position: required
- - y_position: required
- - width: required
- - height: required
- - tag: optional

### GET                         - ( GET base_url/ClassifiedAreas )
- RETURNS: collection of \<classified_area\>

### PUT                         - ( PUT base_url/ClassifiedAreas/\<ClassifiedAreas.public_id\> )
- json_data( \<classified_area\>):
- - training_image:             - ( public id of the new training_image that will be the parented )
- - x_position: optional
- - y_position: optional
- - width: optional
- - height: optional
- - tag: optional
### DELETE                      - ( DELETE base_url/ClassifiedAreas/\<ClassifiedAreas.public_id\>)
- returns: 200 if successfull, 404 if no user exists of specified id.


### 'Convenience URLs'
TRAINING_IMAGE_CROPPED          - ( GET base_url/classifiead_areas/\<ClassifiedArea.public_id\>/training_image_cropped)

