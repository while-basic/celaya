# ----------------------------------------------------------------------------
#  File:        replace_celaya.sh
#  Project:     Celaya Solutions (Rebranding)
#  Created by:  Celaya Solutions, 2025
#  Author:      Christopher Celaya <chris@celayasolutions.com>
#  Description: Script to replace all occurrences of "celaya" with "celaya" in the codebase
#  Version:     1.0.0
#  License:     BSL (SPDX id BUSL)
#  Last Update: (May 2025)
# ----------------------------------------------------------------------------

#!/bin/bash

set -e

echo "Starting rebranding process: Replacing 'celaya' with 'celaya' across the codebase..."

# Replace in Go import paths
find . -type f -name "*.go" -exec sed -i '' 's|github.com/celaya/celaya|github.com/celaya/celaya|g' {} \;
echo "Updated Go import paths"

# Replace in Go module references
find . -type f -name "go.mod" -o -name "go.sum" -exec sed -i '' 's|github.com/celaya/celaya|github.com/celaya/celaya|g' {} \;
echo "Updated Go module references"

# Replace in shell scripts
find . -type f -name "*.sh" -exec sed -i '' 's/celaya/celaya/g' {} \;
echo "Updated shell scripts"

# Replace in Dockerfiles
find . -type f -name "Dockerfile*" -exec sed -i '' 's/celaya/celaya/g' {} \;
echo "Updated Dockerfiles"

# Replace in yaml files
find . -type f -name "*.yaml" -o -name "*.yml" -exec sed -i '' 's/celaya/celaya/g' {} \;
echo "Updated YAML files"

# Replace in markdown files
find . -type f -name "*.md" -exec sed -i '' 's/celaya/celaya/g' {} \;
echo "Updated markdown files"

# Replace in package.json files
find . -type f -name "package.json" -exec sed -i '' 's/celaya/celaya/g' {} \;
echo "Updated package.json files"

# Replace in workflow files
find .github/workflows -type f -exec sed -i '' 's/celaya/celaya/g' {} \;
echo "Updated GitHub workflow files"

# Special handling for URLs and domains (with case-insensitive matching)
find . -type f -not -path "*/\.*" -exec sed -i '' 's/celaya\.org/celayasolutions.com/g' {} \;
find . -type f -not -path "*/\.*" -exec sed -i '' 's/celaya\.ai/celayasolutions.com/g' {} \;
find . -type f -not -path "*/\.*" -exec sed -i '' 's/celaya\.com/celayasolutions.com/g' {} \;
echo "Updated URLs and domains"

echo "Rebranding complete! Now run 'go mod tidy' to update dependencies." 