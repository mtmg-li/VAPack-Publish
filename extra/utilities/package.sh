#!/usr/bin/bash

NAME='iankerby'
LOCATION='bsu'
OUTPUT_PREFIX='C-'
OUTPUT_SUFFIX='.shar'
JOB_SCRIPT='vasp.slurm'
METADATA_FILE='metadata.yml'
INPUT_FILES=('INCAR' 'POSCAR' 'POTCAR' 'KPOINTS' "${JOB_SCRIPT}" "${METADATA_FILE}")

# Generate an ID, date, and output file for this calculation package
if [[ ! -f "${METADATA_FILE}" ]]; then
  HUMAN_NAME=''
  CALC_ID=$(date +%s%N | sha256sum | head -c 12)
  CALC_DATE=$(date +%Y-%m-%dT%H:%M:%S)
else
  HUMAN_NAME="$(awk '/human_name:/ {$1=""; print $0}' ${METADATA_FILE})"
  CALC_ID="$(awk '/id:/ {print $2}' ${METADATA_FILE})"
  CALC_DATE="$(awk '/created:/ {print $2}' ${METADATA_FILE})"
fi

OUTPUT_FILE="${OUTPUT_PREFIX}${CALC_ID}${OUTPUT_SUFFIX}"

# Instructions embedded before unshar
read -r -d '' PRE_UNSHAR_INSTRUCTIONS <<- EOM
# Pre unshar instructions
if [[ ! -d "C-${CALC_ID}" ]]; then
  mkdir "C-${CALC_ID}"
fi
cd "C-${CALC_ID}"
EOM

# Instructions embedded after unshar
read -r -d '' POST_UNSHAR_INSTRUCTIONS <<- EOM
# Post unshar instructions

if [[ ! "\$1" == "--unpack-only" ]]; then
    sbatch $JOB_SCRIPT || echo "Failed to queue"
fi
EOM

# Pre-script instructions
read -r -d '' PRE_SCRIPT_INSTRUCTIONS <<- EOM
sed -i '/status:/s/:\s*\S*$/: queued/' "$METADATA_FILE"
EOM

# Post-script instructions
read -r -d '' POST_SCRIPT_INSTRUCTIONS <<- EOM
# Update the metadata status
sed -i '/status:/s/:\s*\S*$/: complete/' $METADATA_FILE

# Pack (almost) all the contents into a zip without compression
find . -maxdepth 1 -type f \( -name "OUTCAR" -o -size -100M \) -printf "%P\n" | xargs zip -q -0 -u C-${CALC_ID}.zip 
EOM

# Define main program
main() {
  # Parse the options and execute appropriate functions
  while getopts ':iph' flag; do
    case "${flag}" in
      i) initialize ;;
      p) package ;;
      *) print_usage
         exit 1
         ;;
    esac
  done
}

# Message to print for unknown/help options
print_usage () {
  printf "Usage: jobman.sh -[option(s)]\n"
  printf "  Option\n"
  printf "    n        name <name>\n"
  printf "    i        initialize\n"
  printf "    p        package\n"
  printf "    m        modify\n"
}

# Create metadata for a calculation
initialize() {
  echo "Writing ${METADATA_FILE}..."
  printf -- '---\n' > ${METADATA_FILE}
  printf "human_name: ${HUMAN_NAME}\n" >> ${METADATA_FILE}
  printf "id: ${CALC_ID}\n"  >> ${METADATA_FILE}
  printf "created: ${CALC_DATE}\n" >> ${METADATA_FILE}
  printf "status: initialized\n" >> ${METADATA_FILE}
}

# Find all relevant files and shar them up
package() {
  echo "Packing C-${CALC_ID}"
  # Update metadata
  sed -i '/status:/s/:\s*\S*$/: packaged/' "${METADATA_FILE}"
  # Generate shell archive and force text mode
  shar -T -n "${OUTPUT_PREFIX}${CALC_ID}" -s "${NAME}@${LOCATION}" "${INPUT_FILES[@]}" > "${OUTPUT_FILE}"
  # Strip the source directory information for privacy
  sed -i '/# Source directory was/s/.*$/#/' "${OUTPUT_FILE}"
  # Update the head of the shell archive
  { echo "#!/bin/sh"; echo "${PRE_UNSHAR_INSTRUCTIONS}"; tail -n +2 "${OUTPUT_FILE}"; } > "${OUTPUT_FILE}.tmp"
  # Update the tail of the shell archive
  head -n -1 "${OUTPUT_FILE}.tmp" > "${OUTPUT_FILE}"
  echo "${POST_UNSHAR_INSTRUCTIONS}" >> "${OUTPUT_FILE}"
  echo "exit 0" >> ${OUTPUT_FILE}
  rm "${OUTPUT_FILE}.tmp"
  # If a temporary copy of the job script was created, restore the original
  if [[ -e "${JOB_SCRIPT}.tmp" ]]; then
    mv "${JOB_SCRIPT}.tmp" "${JOB_SCRIPT}"
  fi
}

# Modify the slurm script to clean up when done
modify() {
  echo "Modifying ${JOB_SCRIPT}"
  SLURM_PREPROCESS_END=$(grep -n "#SBATCH" "${JOB_SCRIPT}" | tail -n 1 | cut -f1 -d:)
  cp "${JOB_SCRIPT}" "${JOB_SCRIPT}.tmp"
  # Copy the slurm commands to the start
  head -n $SLURM_PREPROCESS_END "${JOB_SCRIPT}.tmp" > "${JOB_SCRIPT}"
  echo "" >> "${JOB_SCRIPT}"
  # Copy the pre_script instructions
  echo "${PRE_SCRIPT_INSTRUCTIONS}" >> "${JOB_SCRIPT}"
  echo "" >> "${JOB_SCRIPT}"
  # Copy the remainder of the original script
  tail -n $SLURM_PREPROCESS_END "${JOB_SCRIPT}.tmp" >> "${JOB_SCRIPT}"
  echo "" >> "${JOB_SCRIPT}"
  # Write the post_script instructions
  echo "${POST_SCRIPT_INSTRUCTIONS}" >> "${JOB_SCRIPT}"
}

# Preprocess high priority flags
passThrough=()
while getopts ':n:m' flag; do
  case "${flag}" in
    n) HUMAN_NAME="${OPTARG}" ; echo "Naming calculation: ${OPTARG}" ;;
    m) modify ;;
    *) passThrough+=( "-${OPTARG}" )
       if [[ ${@: OPTIND:1} != -* ]]; then
         passThrough+=( "${@: OPTIND:1}" )
         (( ++OPTIND ))
       fi
       ;;
  esac
done
# Reset option index
OPTIND=1

# Execute main function with all passthrough arguments
main "${passThrough[@]}"

