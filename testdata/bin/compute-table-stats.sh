#!/bin/bash
# Copyright (c) 2012 Cloudera, Inc. All rights reserved.
# Runs compute table stats over a curated set of Impala test tables.
#
set -euo pipefail
trap 'echo Error in $0 at line $LINENO: $(cd "'$PWD'" && awk "NR == $LINENO" $0)' ERR

. ${IMPALA_HOME}/bin/impala-config.sh > /dev/null 2>&1
COMPUTE_STATS_SCRIPT="${IMPALA_HOME}/tests/util/compute_table_stats.py"

# Run compute stats over as many of the tables used in the Planner tests as possible.
${COMPUTE_STATS_SCRIPT} --db_names=functional\
    --table_names="alltypes,alltypesagg,alltypesaggmultifilesnopart,alltypesaggnonulls,
    alltypessmall,alltypestiny,jointbl,dimtbl"

# We cannot load HBase on s3 and isilon yet.
if [ "${TARGET_FILESYSTEM}" = "hdfs" ]; then
  ${COMPUTE_STATS_SCRIPT} --db_name=functional_hbase\
    --table_names="alltypessmall,stringids"
fi
${COMPUTE_STATS_SCRIPT} --db_names=tpch,tpch_parquet \
    --table_names=customer,lineitem,nation,orders,part,partsupp,region,supplier
${COMPUTE_STATS_SCRIPT} --db_names=tpch_nested_parquet
${COMPUTE_STATS_SCRIPT} --db_names=tpcds

if "$KUDU_IS_SUPPORTED"; then
  ${COMPUTE_STATS_SCRIPT} --db_names=functional_kudu --table_names=zipcode_incomes
  ${COMPUTE_STATS_SCRIPT} --db_names=tpch_kudu
fi

