# You need to start Xvfb before running processing-java
Xvfb :99 -screen 0 1024x768x24 &
sleep 10
export DISPLAY=:99

# Run
SAVE_DIR=$1
OBJS=$(ls ${SAVE_DIR})
for OBJ in ${OBJS}; do
    # if there is an *.png file, then skip
    if [ -f "${SAVE_DIR}/${OBJ}/${OBJ}.png" ]; then
        echo "Skipping ${SAVE_DIR}/${OBJ}"
    fi
    timeout 30 ${PROCESSING} --sketch="${SAVE_DIR}/${OBJ}" --run
done

# Kill Xvfb after finish
sleep 10
pkill -9 Xvfb
