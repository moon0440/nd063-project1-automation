# https://console.aws.amazon.com/vpc/home?region=us-east-1#vpcs:search=vpc-050fe8a080ce80090;sort=VpcId
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import boto3
import pprint
import secrets
import string
import time

USER = 'selenium'


def create_selenium_user():
    password = ''.join(secrets.choice(string.printable[:-6]) for i in range(128))
    # TODO move this to cloudformation stack
    iam = boto3.resource('iam')
    user = iam.create_user(
        UserName=USER
    )
    user.attach_policy(
        PolicyArn='arn:aws:iam::aws:policy/job-function/ViewOnlyAccess'
    )
    user.create_login_profile(
        Password=password,
        PasswordResetRequired=False
    )
    return user, password


def remove_selenium_user(user):
    for p in user.attached_policies.iterator():
        user.detach_policy(PolicyArn=p.arn)
    boto3.client('iam').delete_login_profile(UserName=user.name)
    user.delete()
    # TODO add assertion account has been removed


def get_with_login(url, file_name="screenshot.png", user=None, password=None):
    account_id = boto3.client('sts').get_caller_identity().get('Account')
    # TODO Takes a bit for the account to be created so need to add check that the selenium account is avail for login
    time.sleep(20)
    options = webdriver.ChromeOptions()
    options.add_argument('headless')
    # set the window size
    options.add_argument('window-size=1920x1080')
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=options)
    driver.implicitly_wait(20)

    driver.get(url)
    driver.find_element_by_id('aws-signin-general-user-selection-iam').click()
    driver.find_element_by_id('resolving_input').send_keys(account_id)
    driver.find_element_by_id('next_button').click()
    driver.save_screenshot(file_name)

    driver.find_element_by_id('username').send_keys(user)
    driver.find_element_by_id('password').send_keys(password)
    driver.find_element_by_id('signin_button').click()

    # TODO Uggh selenium race/wait conditions...
    time.sleep(20)
    driver.save_screenshot(file_name)


def create(url, file_name="screenshot.png"):
    user, password = create_selenium_user()
    try:
        get_with_login(url, file_name=file_name, user=user.name, password=password)
    finally:
        # Insures at at least and attempt to remove the user account
        remove_selenium_user(user)


def vpc_console_url(vpc_id, region):
    return f"https://console.aws.amazon.com/vpc/home?region={region}#vpcs:search={vpc_id}"


def create_vpc_screenshot(vpc_id, region, file_name):
    url = vpc_console_url(vpc_id, region)
    create(url, file_name)


if __name__ == "__main__":
    url = "https://console.aws.amazon.com/vpc/home?region=us-east-1#vpcs:search=vpc-050fe8a080ce80090;sort=VpcId"
    create(url=url, file_name="primary_Vpc.png")
