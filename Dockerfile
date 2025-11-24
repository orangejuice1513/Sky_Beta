# 
# inherit ros2 
FROM ros:humble 

# all the shit u gotta run first 
RUN apt-get update && apt-get install -y\
git \
python3-pip \
neovim \
build-essential \
cmake \
gdb \
wget

# default folder after logging in 
WORKDIR /home/julia/Sky/Sky-Beta

# source ros2 
RUN echo "source opt/ros/humble/setup.bash" >> ~/.bashrc


