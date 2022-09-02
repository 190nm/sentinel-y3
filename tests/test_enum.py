from enum import Enum, Flag, auto

class Permissions(Flag):
    NULL = 0
    EXECUTE = auto()
    WRITE = auto()
    READ = auto()

class APIEndpoints(Enum):

    def __str__(self):
        return f"http://app.yuyuyui.jp/api/v1/{self.value}"

    requirement_versions = "requirement_versions"
    resource_versions = "resource_versions/{0}"
    sessions = "sessions"
    shop_transaction = "shops/{0}/products/{1}/transactions/{2}"
    

def testfunc(method: str, endpoint: Enum, *endpoint_args, request_body=None) -> object:
    if request_body:
        request_body = "yes lol"
    print(method, str(endpoint).format(*endpoint_args), request_body)


# testfunc("POST", APIEndpoints.sessions, request_body="abcdefg")
# testfunc("POST", APIEndpoints.shop_transaction, "A21F", "B921", "CC52", request_body="abcdefg")
# testfunc("GET", APIEndpoints.resource_versions, "scenario_common")
RW = Permissions.NULL
RW |= Permissions.READ
print(RW)
RW |= Permissions.WRITE
print(RW)
if Permissions.EXECUTE in RW:
    print("Yay")