#!/usr/bin/env bash

usage() { echo "Usage: $0 FILE [-y <height>] [-w <width>] [-e <end>]" 1>&2; exit 1; }

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

if [[ ! ${FILE##*/} == "OSZICAR" ]]; then
    echo "Must be an OSZICAR file (including name)"
    exit 1
fi
shift

# Defaults
HEIGHT=20
WIDTH=$(tput cols)
START=1
END=0

while getopts ':y:w:e:' opt; do
    case "${opt}" in
        y) HEIGHT=${OPTARG} ;;
        w) WIDTH=${OPTARG} ;;
        e) END=${OPTARG} ;;
        *)
            usage
            ;;
    esac
done

N=$(grep -cEe '^\s*[0-9]+ F=' "$FILE")
if [[ ! $END == 0 ]]
then
    N=$END
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

BEGIN {
    CONVFMT = "%.6g"
    # Maximum of 8 for energy label plus axis line
    width = vwidth-14
    # 2 lines for axis line and label
    height = vheight-2
    if (width < 10 || height < 3)
    {
        printf "Viewport is too small!!!\n"
        failure = 1
        exit
    }
    data[1] = 0
    for (i=2;i<=width;i++)
    {
        key = int(i/width*n)
        data[key] = 0
    }
    title = "Energy plot from OSZICAR"
    padding = int((vwidth-length(title))/2)
    printspace(padding)
    printf "%s", title
    printspace(padding)
    printf "\n"
}

/^\s*[0-9]+ F=/ {
    if ($1 in data)
        data[$1] = strtonum($3)
}

END {
    # Quit if the program failed earlier
    if (failure)
        exit 1
    # Get the maximum and minimum energy values in the dataset
    # Is possible to accidentally skip peaks
    nrgmax = data[1]
    nrgmin = data[1]
    for (i in data)
    {
        if (nrgmax < data[i])
            nrgmax = data[i]
        if (nrgmin > data[i])
            nrgmin = data[i]
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
    for (j=1;j<=height;j++)
    {
        line = join(viewdata[j], 1, width, SUBSEP)
        if (j==1)
        {
            printspace(8-length(nrgmax ""))
            printf "%.6g eV |", nrgmax
        }
        else if (j==int(height/2))
            printf "   Energy   |"
        else if (j==height)
            printf "%.6g eV |", nrgmin
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
    printf "             1"
    n_strl = length(n "")
    xpadding = (vwidth-20-n_strl)/2
    printspace(xpadding)
    printf "Step"
    printspace(xpadding)
    printf "%d\n", n
}
EOF

awk -v vwidth=$WIDTH -v vheight=$HEIGHT -v n=$N -v start=$START "$PLOTSCRIPT" "$FILE"
