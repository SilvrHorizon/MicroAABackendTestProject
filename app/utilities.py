import re

# From geeksforgeeks: https://www.geeksforgeeks.org/check-if-email-address-valid-or-not-in-python/
def email_is_valid(to_check):
    email_regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
    if(re.search(email_regex, to_check)):  
        return True
    return False