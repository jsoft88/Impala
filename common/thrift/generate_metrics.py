#!/usr/bin/env python
# Copyright 2015 Cloudera Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys
import os
import re
import collections
from optparse import OptionParser
try:
  import json
except ImportError:
  import simplejson as json # For Python 2.4

THRIFT_DIR = os.path.join(os.getenv('IMPALA_HOME'), 'common/thrift')

parser = OptionParser()
parser.add_option("-i", dest="input_schema_path",
                  default=os.path.join(THRIFT_DIR, "metrics.json"),
                  help="The path of the output mdl file. Default: %default")
parser.add_option("--generate_thrift", dest="generate_thrift",
                  action="store_true", default=True,
                  help="Generates the metric thrift definitions. Default: %default")
parser.add_option("--generate_mdl", dest="generate_mdl",
                  action="store_true", default=False,
                  help="Generates a CM-compatible mdl file. Default: %default")
parser.add_option("-o", dest="output_thrift_path",
                  default=os.path.join(THRIFT_DIR, "MetricDefs.thrift"),
                  help="The path of the output MetricDefs thrift file. Default: %default")
parser.add_option("--output_mdl_path", dest="output_mdl_path",
                  default="/tmp/impala_schema.mdl",
                  help="The path of the output mdl file. Default: %default")
# TODO: get default version value from bin/save-version.sh
parser.add_option("--output_mdl_version", dest="output_mdl_version",
                  metavar="IMPALA_VERSION", default="2.5.0-cdh5",
                  help="The Impala version that is written in the output mdl.")

options, args = parser.parse_args()

def load_metrics(source_file):
  """Reads the json file of metric definitions and returns a map of metric names to
     metric definitions"""
  raw_metrics = json.loads(open(source_file).read())
  metrics = { }
  for m in raw_metrics:
    if m['key'] in metrics:
      assert False, "Metric key %s already used, check definition of %s" % (m['key'], m)
    m['kind'] = "Metrics.TMetricKind.%s" % m['kind']
    m['units'] = "Metrics.TUnit.%s" % m['units']
    metrics[m['key']] = m
  return metrics

THRIFT_PREAMBLE = """
// Copyright 2015 Cloudera Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
// http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.
//
//
// THIS FILE IS AUTO GENERATED BY generate_metrics.py DO NOT MODIFY IT BY HAND.
//

namespace cpp impala
namespace java com.cloudera.impala.thrift

include "Metrics.thrift"

// All metadata associated with a metric. Used to instanciate metrics.
struct TMetricDef {
  1: optional string key
  2: optional Metrics.TMetricKind kind
  3: optional Metrics.TUnit units
  4: optional list<string> contexts
  5: optional string label
  6: optional string description
}

"""

def generate_thrift():
  """Generates the thrift metric definitions file used by Impala."""
  metrics = load_metrics(options.input_schema_path)
  metrics_json = json.dumps(metrics, sort_keys=True, indent=2)

  # dumps writes the TMetricKind and TUnit as quoted strings which is not
  # interpreted by the thrift compiler correctly. Need to remove the quotes around
  # the enum values.
  metrics_json = re.sub(r'"(Metrics.TMetricKind.\S+)"', r'\1', metrics_json)
  metrics_json = re.sub(r'"(Metrics.TUnit.\S+)"', r'\1', metrics_json)

  target_file = options.output_thrift_path
  fid = open(target_file, "w")
  try:
    fid.write(THRIFT_PREAMBLE)
    fid.write("const map<string,TMetricDef> TMetricDefs =\n")
    fid.write(metrics_json)
  finally:
    fid.close()
  print("%s created." % target_file)

def metric_to_mdl(m):
  """Returns the metric in the mdl format, or None if the metric isn't supported."""
  # TODO: Stamp out metrics with arguments, e.g. output each rpc call_duration metric.
  if '$0' in m['key']:
    print >>sys.stderr, "Skipping metrics with unbound argument, key=%s" % m['key']
    return None

  # TODO: Stamp out individual metrics for other metric types.
  SUPPORTED_METRIC_KINDS = ['COUNTER', 'GAUGE']
  if m['kind'] not in SUPPORTED_METRIC_KINDS:
    print >>sys.stderr, "Skipping %s metric %s" % (m['kind'], m['key'])
    return None

  return dict(
    context=(m['key']),
    name=('impala_' + m['key'].lower().replace('-', '_').replace('.', '_')),
    counter=(m['kind'] == 'COUNTER'),
    numeratorUnit=m['units'].lower(),
    description=m['description'],
    label=m['label'])


# Base MDL for the Impala Service. Does not contain metrics.
MDL_BASE = """
{
  "name" : "IMPALA",
  "version" : "$PROJECT_VERSION",
  "nameForCrossEntityAggregateMetrics" : "impalas",
  "roles" : [
    {
      "name" : "IMPALAD",
      "nameForCrossEntityAggregateMetrics" : "impalads"
    },
    {
      "name" : "STATESTORE",
      "nameForCrossEntityAggregateMetrics" : "statestores"
    },
    {
      "name" : "CATALOGSERVER",
      "nameForCrossEntityAggregateMetrics" : "catalogservers"
    },
    {
      "name" : "LLAMA",
      "nameForCrossEntityAggregateMetrics" : "llamas"
    }
  ],
  "metricEntityTypeDefinitions" : [
      {
        "name" : "IMPALA_POOL",
        "nameForCrossEntityAggregateMetrics" : "impala_pools",
        "entityNameFormat" :  [
           "serviceName",
           "poolName"
        ],
        "label" : "Impala Pool",
        "labelPlural" : "Impala Pools",
        "description" : "A resource pool within which Impala schedules queries.",
        "immutableAttributeNames" : [
           "poolName",
           "serviceName"
        ]
      },
      {
        "name" : "IMPALA_DAEMON_POOL",
        "nameForCrossEntityAggregateMetrics" : "impala_daemon_pools",
        "entityNameFormat" : [
           "roleName",
           "poolName"
        ],
        "label" : "Impala Daemon Pool",
        "labelPlural" : "Impala Daemon Pools",
        "description" : "An Impala Daemon's view of a specific Impala resource pool.",
        "immutableAttributeNames" : [
           "poolName",
           "roleName",
           "serviceName"
        ],
        "parentMetricEntityTypeNames" : [
            "IMPALA_POOL",
            "IMPALA-IMPALAD"
        ]
      }
    ]
}
"""

def generate_mdl():
  """Generates the CM compatible metric definition (MDL) file."""
  metrics = []
  input_file = open(options.input_schema_path)
  try:
    metrics = json.load(input_file)
  finally:
    input_file.close()

  # A map of entity type -> [metric dicts].
  metrics_by_role = collections.defaultdict(lambda: [])
  for m in metrics:
    # Convert to the format that CM expects.
    mdl_metric = metric_to_mdl(m)
    if mdl_metric is None:
      continue
    for ctx in m['contexts']:
      metrics_by_role[ctx].append(mdl_metric)

  mdl = json.loads(MDL_BASE)
  mdl['version'] = options.output_mdl_version
  for role in mdl['roles']:
    role_metrics = []
    if metrics_by_role.has_key(role['name']):
      role_metrics = metrics_by_role[role['name']]
    role['metricDefinitions'] = role_metrics

  target_file = options.output_mdl_path
  fid = open(target_file, "w")
  try:
    fid.write(json.dumps(mdl, indent=4))
  finally:
    fid.close()
  print("%s created." % target_file)

if __name__ == "__main__":
  if options.generate_thrift:
    generate_thrift()

  if options.generate_mdl:
    generate_mdl()
