import boto3
import os
from jinja2 import Template

def get_username():
    response = sts_client.get_caller_identity()
    return response["Arn"].replace("arn:aws:iam::" + response["Account"] + ":user/","")

def get_accounts(role_name,source_profile,session_name):
    aws_accounts = []
    
    next_token = None
    while True:
        if next_token != None:
            r = org_client.list_accounts(
                NextToken=next_token
            )
        else:
            r = org_client.list_accounts()

        for a in r["Accounts"]:
            aws_account = {}

            for b in aws_regions:
                if b in a["Name"]:
                    account_region = b

            for c in environments:
                if c in a["Name"]:
                    environment = c

            if a["Name"] not in [aws_profile]:
                aws_account["id"] = a["Id"]
                aws_account["profile_name"] = a["Name"]
                aws_account["role_name"] = role_name
                aws_account["source_profile"] = source_profile
                aws_account["session_name"] = session_name

                aws_accounts.append(aws_account)


        if "NextToken" in r:
            next_token = r["NextToken"]
        else:
            break

    return aws_accounts

def build_default(aws_region,default_output):
    t = Template("""[default]
region = {{aws_region}}
output = {{default_output}}""")

    return t.render(aws_region=aws_region)


def build_config(aws_accounts):

    t = Template(""" {% for item in items%}
[profile {{item.profile_name}}]
role_arn = arn:aws:iam::{{item.id}}:role/{{item.role_name}}
source_profile = {{item.source_profile}}
role_session_name = {{item.session_name}}
region = {{item.region}}
https://signin.aws.amazon.com/switchrole?roleName={{item.role_name}}&account={{item.profile_name}}

{% endfor %}""")

    return t.render(items=aws_accounts)

def build_html(aws_accounts):

    t = Template(""" <HTML>
    <head>

    </head>
    <body>
    <table border="1" cellpadding="0" cellspacing="0">
    <tr>
        <td>id
        </td>
        <td>name
        </td>
        <td>url
        </td>
    </tr>
{% for item in items%}
    <tr>
        <td>{{item.id}}
        </td>
        <td>{{item.profile_name}}
        </td>
        <td>
        <a href="https://signin.aws.amazon.com/switchrole?roleName={{item.role_name}}&account={{item.profile_name}}">{{item.profile_name}}</a><br>
        </td>
    </tr>
{% endfor %}
        </table>
    </body>
</HTML>""")

    return t.render(items=aws_accounts)

def write_to_file(obj_write,output_file):
    f = open(os.path.expanduser(output_file),"w+")
    f.write(str(obj_write))
    f.close()

if __name__ == "__main__":
    aws_profile = "default"
    aws_region = "eu-west-2"
    aws_role = "OrganizationAccountAccessRole"
    aws_output = "json"
    file_config = "~/.aws/config"
    file_html = "~/index.html"

    session = boto3.Session(profile_name=aws_profile,region_name=aws_region)
    ec2_client = session.client("ec2")
    org_client = session.client("organizations")
    sts_client = session.client("sts")
    
    aws_accounts = get_accounts(aws_role,aws_profile,get_username())

    aws_config = build_config(aws_accounts)

    default_config = build_default(aws_region,aws_output)
    write_to_file(default_config + "\n" + aws_config,file_config)

    html_helper = build_html(aws_accounts)
    write_to_file(html_helper,file_html)