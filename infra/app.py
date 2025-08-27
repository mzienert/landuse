#!/usr/bin/env python3

import aws_cdk as cdk
from constructs import Construct

from stacks.landuse_stack import LanduseStack


app = cdk.App()

# Get environment from context or default to dev
env_name = app.node.try_get_context("env") or "dev"

# Define environment-specific configurations
environments = {
    "dev": {
        "account": app.node.try_get_context("dev_account"),
        "region": app.node.try_get_context("dev_region") or "us-west-2"
    },
    "staging": {
        "account": app.node.try_get_context("staging_account"),
        "region": app.node.try_get_context("staging_region") or "us-west-2"
    },
    "prod": {
        "account": app.node.try_get_context("prod_account"),
        "region": app.node.try_get_context("prod_region") or "us-west-2"
    }
}

env_config = environments.get(env_name, environments["dev"])

# Create the stack with environment-specific configuration
LanduseStack(
    app,
    f"LanduseStack-{env_name}",
    env=cdk.Environment(
        account=env_config["account"],
        region=env_config["region"]
    ),
    env_name=env_name,
    description=f"La Plata County RAG System - {env_name.capitalize()} Environment"
)

app.synth()