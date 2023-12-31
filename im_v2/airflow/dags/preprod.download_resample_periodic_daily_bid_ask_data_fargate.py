# This is a utility DAG to conduct QA on real time data download
# DAG task downloads data for last N minutes in one batch

import copy
import datetime
import os
from itertools import product

import airflow
from airflow.contrib.operators.ecs_operator import ECSOperator
from airflow.models import Variable
from airflow.operators.dummy_operator import DummyOperator

_FILENAME = os.path.basename(__file__)

# This variable will be propagated throughout DAG definition as a prefix to
# names of Airflow configuration variables, allow to switch from test to preprod/prod
# in one line (in best case scenario).
_STAGE = _FILENAME.split(".")[0]
assert _STAGE in ["prod", "preprod", "test"]

# Used for seperations of deployment environments
# ignored when executing on prod/preprod.
_USERNAME = ""

# Deployment type, if the task should be run via fargate (serverless execution)
# or EC2 (machines deployed in our auto-scaling group)
_LAUNCH_TYPE = "fargate"
assert _LAUNCH_TYPE in ["ec2", "fargate"]

_DAG_ID = _FILENAME.rsplit(".", 1)[0]
_EXCHANGES = ["binance"]
_VENDORS = ["crypto_chassis"]
_UNIVERSES = {"crypto_chassis": "v3"}
# _CONTRACTS = ["spot", "futures"]
_CONTRACTS = ["futures"]
_DATA_TYPES = ["bid_ask"]
# These values are changed dynamically based on DAG purpose and nature
#  of the downloaded data
_DOWNLOAD_MODE = "periodic_daily"
_ACTION_TAG = "downloaded_1sec"
_DATA_FORMAT = "parquet"
# The value is implicit since this is an Airflow DAG.
_DOWNLOADING_ENTITY = "airflow"
_DATASET_VERSION = "v1_0_0"
_BID_ASK_DEPTH = "{{ var.value.historical_download_bid_ask_depth }}"
_DAG_DESCRIPTION = (
    f"Daily {_DATA_TYPES} data download and resampling, contracts:"
    + f"{_CONTRACTS}, using {_VENDORS} from {_EXCHANGES}."
)
_SCHEDULE = Variable.get(f"{_DAG_ID}_schedule")

# Used for container overrides inside DAG task definition.
# If this is a test DAG don't forget to add your username to container suffix.
# i.e. cmamp-test-juraj since we try to follow the convention of container having
# the same name as task-definition if applicable
# Set to the name your task definition is suffixed with i.e. cmamp-test-juraj,
_CONTAINER_SUFFIX = f"-{_STAGE}" if _STAGE in ["preprod", "test"] else ""
_CONTAINER_SUFFIX += f"-{_USERNAME}" if _STAGE == "test" else ""
_CONTAINER_NAME = f"cmamp{_CONTAINER_SUFFIX}"

ecs_cluster = Variable.get(f"{_STAGE}_ecs_cluster")
# The naming convention is set such that this value is then reused
# in log groups, stream prefixes and container names to minimize
# convolution and maximize simplicity.
ecs_task_definition = _CONTAINER_NAME

# Subnets and security group is not needed for EC2 deployment but
# we keep the configuration header unified for convenience/reusability.
ecs_subnets = [Variable.get("ecs_subnet1"), Variable.get("ecs_subnet3")]
ecs_security_group = [Variable.get("ecs_security_group")]
ecs_awslogs_group = f"/ecs/{ecs_task_definition}"
ecs_awslogs_stream_prefix = f"ecs/{ecs_task_definition}"
s3_bucket_path = f"s3://{Variable.get(f'{_STAGE}_s3_data_bucket')}"

# Pass default parameters for the DAG.
default_args = {
    "retries": 0,
    "email": [Variable.get(f"{_STAGE}_notification_email")],
    "email_on_failure": True,
    "email_on_retry": False,
    "owner": "airflow",
}

# Create a DAG.
dag = airflow.DAG(
    dag_id=_DAG_ID,
    description=_DAG_DESCRIPTION,
    max_active_runs=1,
    default_args=default_args,
    schedule_interval=_SCHEDULE,
    catchup=True,
    start_date=datetime.datetime(2022, 12, 7, 0, 0, 0),
)

download_command = [
    "/app/amp/im_v2/common/data/extract/download_bulk.py",
    # Calculate timestamp to download data from the entire past day
    "--end_timestamp '{{ data_interval_end.replace(hour=0, minute=0, second=0) - macros.timedelta(seconds=1) }}'",
    "--start_timestamp '{{ data_interval_start.replace(hour=0, minute=0, second=0) }}'",
    "--exchange_id '{}'",
    "--universe '{}'",
    "--data_type '{}'",
    "--vendor '{}'",
    "--contract_type '{}'",
    "--aws_profile 'ck'",
    # The command needs to be executed manually first because --incremental
    # assumes appending to existing folder.
    "--incremental",
    f"--bid_ask_depth {_BID_ASK_DEPTH}",
    f"--s3_path '{s3_bucket_path}'",
    f"--download_mode '{_DOWNLOAD_MODE}'",
    f"--downloading_entity '{_DOWNLOADING_ENTITY}'",
    f"--action_tag '{_ACTION_TAG}'",
    f"--data_format '{_DATA_FORMAT}'",
]

resample_command = [
    "/app/amp/im_v2/common/data/transform/resample_daily_bid_ask_data.py",
    "--end_timestamp '{{ data_interval_end.replace(hour=0, minute=0, second=0) - macros.timedelta(seconds=1) }}'",
    "--start_timestamp '{{ data_interval_start.replace(hour=0, minute=0, second=0) }}'",
    "--src_dir '{}'",
    "--dst_dir '{}'",
]

start_task = DummyOperator(task_id="start_dag", dag=dag)
end_download = DummyOperator(task_id="end_dag", dag=dag)

for vendor, exchange, contract, data_type in product(
    _VENDORS, _EXCHANGES, _CONTRACTS, _DATA_TYPES
):

    # TODO(Juraj): Make this code more readable.
    # Do a deepcopy of the bash command list so we can reformat params on each iteration.
    curr_bash_command = copy.deepcopy(download_command)
    curr_bash_command[3] = curr_bash_command[3].format(exchange)
    curr_bash_command[4] = curr_bash_command[4].format(_UNIVERSES[vendor])
    curr_bash_command[5] = curr_bash_command[5].format(data_type)
    curr_bash_command[6] = curr_bash_command[6].format(vendor)
    curr_bash_command[7] = curr_bash_command[7].format(contract)

    kwargs = {}
    kwargs["network_configuration"] = {
        "awsvpcConfiguration": {
            "securityGroups": ecs_security_group,
            "subnets": ecs_subnets,
        },
    }

    downloading_task = ECSOperator(
        task_id=f"{_DOWNLOAD_MODE}.download.{vendor}.{exchange}.{data_type}.{contract}",
        dag=dag,
        aws_conn_id=None,
        cluster=ecs_cluster,
        task_definition=ecs_task_definition,
        launch_type=_LAUNCH_TYPE.upper(),
        overrides={
            "containerOverrides": [
                {
                    "name": _CONTAINER_NAME,
                    "command": curr_bash_command,
                }
            ],
            "cpu": "1024",
            "memory": "4096",
        },
        awslogs_group=ecs_awslogs_group,
        awslogs_stream_prefix=ecs_awslogs_stream_prefix,
        execution_timeout=datetime.timedelta(minutes=30),
        **kwargs,
    )

    # TODO(Juraj): Make this code more readable.
    # Do a deepcopy of the bash command list so we can reformat params on each iteration.
    curr_bash_command = copy.deepcopy(resample_command)
    curr_bash_command[-2] = curr_bash_command[-2].format(
        os.path.join(
            s3_bucket_path,
            # TODO(Juraj): remove this hardocded value.
            "v3",
            _DOWNLOAD_MODE,
            _DOWNLOADING_ENTITY,
            _ACTION_TAG,
            _DATA_FORMAT,
            data_type,
            contract,
            _UNIVERSES[vendor],
            vendor,
            exchange,
            _DATASET_VERSION,
        )
    )
    curr_bash_command[-1] = curr_bash_command[-1].format(
        os.path.join(
            s3_bucket_path,
            # TODO(Juraj): remove this hardocded value.
            "v3",
            _DOWNLOAD_MODE,
            _DOWNLOADING_ENTITY,
            "resampled_1min",
            _DATA_FORMAT,
            data_type,
            contract,
            _UNIVERSES[vendor],
            vendor,
            exchange,
            _DATASET_VERSION,
        )
    )

    resampling_task = ECSOperator(
        task_id=f"resample.{vendor}.{exchange}.{data_type}.{contract}",
        dag=dag,
        aws_conn_id=None,
        cluster=ecs_cluster,
        task_definition=ecs_task_definition,
        launch_type=_LAUNCH_TYPE.upper(),
        overrides={
            "containerOverrides": [
                {
                    "name": _CONTAINER_NAME,
                    "command": curr_bash_command,
                }
            ],
            "cpu": "1024",
            "memory": "4096",
        },
        awslogs_group=ecs_awslogs_group,
        awslogs_stream_prefix=ecs_awslogs_stream_prefix,
        execution_timeout=datetime.timedelta(minutes=30),
        **kwargs,
    )

    start_task >> downloading_task >> resampling_task >> end_download
