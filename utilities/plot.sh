#!/usr/bin/env bash

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )

usage() { echo "Usage: $0 FILE [-y <height>] [-w <width>] [-b <begin>] [-e <end>]" 1>&2; exit 1; }

# OSZICAR file
FILE=$1

if [[ $FILE =~ ^- ]]
then
    if [[ "$FILE" =~ ^-+h ]]
    then
        usage
    fi
    echo "Must lead with FILE"
    exit 1
fi

if ! $(head -n 1 "$FILE" | grep -qEe 'N\s*E\s*dE\s*d eps\s*ncg\s*rms\s*rms\(c\)')
then
    if ! $(head -n 1 "$FILE" | grep -qEe 'vasp\.[56].*')
    then
        echo "Are you sure this is an OSZICAR or OUTCAR file?"
        exit 1
    else
        IS_OUTCAR=1
    fi
else
    IS_OSZICAR=1
fi

shift

# Defaults
HEIGHT=20
WIDTH=$(tput cols)
START=1
END=0
SEARCH_TAG="E"

while getopts ':y:w:b:e:F' opt; do
    case "${opt}" in
        y)  HEIGHT=${OPTARG} ;;
        w)  WIDTH=${OPTARG} ;;
        b)  START=${OPTARG} ;;
        e)  END=${OPTARG} ;;
        F)  SEARCH_TAG="F" ;;
        *)
            usage
            ;;
    esac
done

if [[ "$SEARCH_TAG" == "E" ]]
then
    if ! $(head -n 1 "$FILE" | grep -qEe 'N\s*E\s*dE\s*d eps\s*ncg\s*rms\s*rms\(c\)')
    then
        echo "Are you sure this is an OSZICAR file?"
        exit 1
    else
        N=$(grep -cEe '^\s*[0-9]+ F=' "$FILE")
    fi

elif [[ "$SEARCH_TAG" == "F" ]]
then
    if ! $(head -n 1 "$FILE" | grep -qEe 'vasp\.[56].*')
    then
        echo "Are you sure this is an OUTCAR file?"
        exit 1
    else
        N=$(grep -cEe '-+ Ionic step\s*[0-9]+\s*-+' "$FILE")
    fi

else
    echo "Unknown search tag"
    exit 1
fi

if (( $END == 0 ))
then
    END=$N
elif (( $END > $N ))
then
    echo "End value cannot exceed final step value"
    exit 1
fi

if (( $START < 1 ))
then
    echo "Starting index cannot be lower than 1"
    exit 1
fi

if (( $END < $START ))
then
    echo "Starting index cannot preceed ending"
    exit 1
fi

read -r -d '' PLOTSCRIPT << 'EOF'
function join(array, start, end, sep,    result, i)
{
    if (sep == "")
       sep = " "
    else if (sep == SUBSEP) # magic value
       sep = ""
    result = array[start]
    for (i = start + 1; i <= end; i++)
        result = result sep array[i]
    return result
}

function printspace(num    ,i)
{
    assert (i>=0)
    for (i=0;i<num;i++)
        printf " "
}

function abs(x)
{
    return ((x < 0.0) ? -x : x)
}

BEGIN {
    # Float to string conversion format. Do not change.
    CONVFMT = "%.6g"
    # Default minimum difference between peaks that can be shown
    tol = 1e-6
    # Set default search tag to E if not provided
    if (! search_tag)
        search_tag = "E"
    # Fail if unrecognized search tag
    if (! search_tag == "E" || ! search_tag == "F")
    {
        printf "Unknown search attribute %s\n", search_tag
        failure = 1
        exit
    }
    # Maximum of 8 for energy label plus axis line
    width = vwidth-14
    if (width > n-s)
    {
        width = n-s
        vwidth = width+14
    }
    # 2 lines for axis line and label
    height = vheight-2
    if (width < 10 || height < 3)
    {
        printf "Viewport is too small!!!\n"
        failure = 1
        exit
    }
    # Prefill the data array with the utilized steps
    data[s] = 0
    for (i=1;i<=width;i++)
    {
        key = int(i/width*(n-s))+s
        data[key] = 0
    }
    if (search_tag == "E")
    {
        title = "Energy plot from OSZICAR"
        ylabel = "Energy"
        unit = " eV "
    }
    else if (search_tag == "F")
    {
        title = "Maximum Force Norm plot from OUTCAR"
        ylabel = "Force "
        unit = "eV/Å"
        get_step = 1
        get_head = 0
        get_force = 0
        get_foot = 0
    }
}

search_tag == "E" && /^\s*[0-9]+ F=/ {
    if ($1 in data)
        data[$1] = strtonum($3)
}

search_tag == "F" && get_step && /-+ Ionic step\s*[0-9]+\s*-+/ {
    if ($4 in data)
    {
        step = $4
        get_step = 0
        get_head = 1
    }
}

search_tag == "F" && get_head && /^\s*POSITION\s+TOTAL-FORCE/ {
    get_head = 0
    get_force = 1
    maxnorm2 = 0
}

search_tag == "F" && get_force && NF == 6 {
    if (! get_foot)
        get_foot = 1
    norm2 = $4*$4 + $5*$5 + $6*$6
    if (norm2 > maxnorm2)
        maxnorm2 = norm2
}

search_tag == "F" && get_foot && /^ -+$/ {
    get_foot = 0
    get_force = 0
    get_step = 1
    data[step] = sqrt(maxnorm2)
}

END {
    # Quit if the program failed earlier
    if (failure)
        exit 1
    # Get the maximum and minimum energy values in the dataset
    # Is possible to accidentally skip peaks
    nrgmax = data[s]
    nrgmin = data[s]
    for (i in data)
    {
        if (nrgmax < data[i])
            nrgmax = data[i]
        if (nrgmin > data[i])
            nrgmin = data[i]
    }
    if (abs(nrgmax-nrgmin) < tol)
    {
        printf "Quantity differences too fine to depict with this utility.\n"
        exit 1
    }
    # Get the energy coverage of each row
    nrgstep = (nrgmax - nrgmin) / height
    # Save the characters 
    marker = "."
    for (j=1;j<=height+1;j++)
    {
        rownrgmax = nrgmax - (j-1)*nrgstep
        rownrgmin = nrgmax - (j+0)*nrgstep
        i=0
        for (step in data)
        {
            if (data[step] <= rownrgmax &&  data[step] >= rownrgmin)
            {
                viewdata[j][i] = marker
            }
            else
                viewdata[j][i] = " "
        i++
        }
    }
    # Print the plot
    padding = int((vwidth-length(title))/2)
    printspace(padding)
    printf "%s", title
    printspace(padding)
    printf "\n"
    for (j=1;j<=height;j++)
    {
        line = join(viewdata[j], 1, width, SUBSEP)
        if (j==1)
        {
            printspace(8-length(nrgmax ""))
            printf "   %.6g |", nrgmax
        }
        else if (j==int(height/2))
            printf "   " ylabel "   |"
        else if (j==int(height/2)+1)
            printf "    "unit"    |"
        else if (j==height)
            printf "   %.6g |", nrgmin
        else
        {
            printf "           "
            printf " |"
        }
        printf "%s\n", line
    }
    printf "            |"
    for (i=0;i<width;i++)
        printf "_"
    printf "\n"
    printf "             %s", s
    s_strl = length(s "")
    n_strl = length(n "")
    xpadding = (vwidth-20-n_strl-s_strl)/2
    printspace(xpadding)
    printf "Step"
    printspace(xpadding)
    printf "%d\n", n
}
EOF

awk -v vwidth=$WIDTH -v vheight=$HEIGHT -v s=$START -v n=$END -v search_tag=$SEARCH_TAG "$PLOTSCRIPT" "$FILE"
# awk -v vwidth=$WIDTH -v vheight=$HEIGHT -v s=$START -v n=$END -v search_tag=$SEARCH_TAG -f "${SCRIPT_DIR}/plot.awk" "$FILE"
