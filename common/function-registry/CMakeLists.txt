# Copyright 2012 Cloudera Inc.
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


cmake_minimum_required(VERSION 2.6)

set(BE_OUTPUT_DIR ${CMAKE_SOURCE_DIR}/be/generated-sources)
set(FE_OUTPUT_DIR ${CMAKE_SOURCE_DIR}/fe/generated-sources/gen-java/com/cloudera/impala/)

# Set output files for dependency tracking
set(CODE_GEN_OUTPUT
  ${FE_OUTPUT_DIR}/builtins/ScalarBuiltins.java
)

# Source python files
set(FUNCTION_REGISTRY_INPUT
  gen_builtins_catalog.py
  impala_functions.py
)

# Run the python scripts
add_custom_command(
  OUTPUT ${CODE_GEN_OUTPUT}
  COMMAND ./gen_builtins_catalog.py
  DEPENDS ${FUNCTION_REGISTRY_INPUT}
  COMMENT "Generating files for builtins."
  VERBATIM
)

add_custom_target(function-registry ALL DEPENDS ${CODE_GEN_OUTPUT})

