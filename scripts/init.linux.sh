# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.
#
# A small helper script to setup the shell environment to use our local
# versions of tools (e.g. cmake, dotnet, etc.)
#
# Note: this is not required, but then the other tools should be available on
# the system PATH.

if [ -z "$BASH" ]; then
    echo "ERROR: This script currently only works using a bash shell." >&2
    return 1
fi

if [[ $0 == $BASH_SOURCE ]]; then
    echo "Please 'source' this file instead of running it:" >&2
    echo "# . $0" >&2
    exit 1
fi

scriptdir=$(dirname "$(readlink -f "$BASH_SOURCE")")
MLOS_ROOT=$(readlink -f "$scriptdir/..")

# Make sure cmake is available.
if ! [ -x "$MLOS_ROOT/tools/cmake/bin/cmake" ] || ! [ -x "$MLOS_ROOT/tools/bin/cmake" ]; then
    if ! "$MLOS_ROOT/scripts/fetch-cmake.sh"; then
        echo "ERROR: Faled to fetch cmake." >&2
        return -1
    fi
fi

# Make sure dotnet is available.
if ! [ -x "$MLOS_ROOT/tools/dotnet/dotnet" ] || ! [ -x "$MLOS_ROOT/tools/bin/dotnet" ]; then
    if ! "$MLOS_ROOT/scripts/fetch-dotnet.sh"; then
        echo "ERROR: Faled to fetch dotnet." >&2
        return -1
    fi
fi
. "$MLOS_ROOT/scripts/dotnet.env"

# Look for local tools first.
export PATH="$MLOS_ROOT/tools/bin:$PATH"
