import os
import stark_core.data_abstraction as data
import stark_core.security as sec
import stark_core.logging as log

ddb_table   = "[[STARK_DDB_TABLE_NAME]]"
bucket_name = "[[STARK_WEB_BUCKET]]"
region_name = os.environ['AWS_REGION']
page_limit  = 10