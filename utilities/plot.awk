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
    data[s] = 0
    for (i=1;i<width;i++)
    {
        key = int(i/width*(n-s))+s
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
    nrgmax = data[s]
    nrgmin = data[s]
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
    printf "             %s", s
    s_strl = length(s "")
    n_strl = length(n "")
    xpadding = (vwidth-20-n_strl-s_strl)/2
    printspace(xpadding)
    printf "Step"
    printspace(xpadding)
    printf "%d\n", n
}