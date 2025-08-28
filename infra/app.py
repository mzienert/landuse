#!/usr/bin/env python3

import aws_cdk as cdk
from constructs import Construct

from stacks.landuse_stack import LanduseStack

app = cdk.App()

# Get environment from context - NO DEFAULT, must be explicitly set
env_name = app.node.try_get_context("env")

if not env_name:
    raise ValueError(
        "Environment must be specified using --context env=<environment>\n"
        "Valid environments: staging, prod\n"
        "Example: cdk deploy --context env=staging"
    )

# Allow dev, staging and prod deployments
if env_name not in ["dev", "staging", "prod"]:
    raise ValueError(
        f"Invalid environment: {env_name}\n"
        "Valid environments: dev, staging, prod\n"
        "Use 'dev' for LocalStack development environment"
    )

# Define environment-specific configurations
environments = {
    "dev": {
        "account": "000000000000",  # LocalStack default account
        "region": "us-west-2"
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

env_config = environments[env_name]

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