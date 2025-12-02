# inherit ros2 
FROM osrf/ros:humble-desktop-full

# all the shit u gotta run first 
RUN apt-get update && apt-get install -y \
neovim \
cmake \
gdb \
wget

ARG USERNAME=appuser
ARG USER_UID=1000
ARG USER_GID=$USER_UID

# Create the user, the group, and give them password-less sudo access
RUN groupadd --gid $USER_GID $USERNAME \
    && useradd --uid $USER_UID --gid $USER_GID -m $USERNAME \
    && echo $USERNAME ALL=\(root\) NOPASSWD:ALL > /etc/sudoers.d/$USERNAME \
    && chmod 0440 /etc/sudoers.d/$USERNAME

RUN git clone https://github.com/eProsima/Micro-XRCE-DDS-Agent.git /tmp/Micro-XRCE-DDS-Agent \
    && cd /tmp/Micro-XRCE-DDS-Agent \
    && mkdir build && cd build \
    && cmake .. \
    && make \
    && make install \
    && ldconfig /usr/local/lib/ \
    && rm -rf /tmp/Micro-XRCE-DDS-Agent\
    && pip3 install kconfiglib jinja2 jsonschema future
    

USER $USERNAME

# default folder after logging in 
WORKDIR /home/appuser/sky

# source ros2 
RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc


