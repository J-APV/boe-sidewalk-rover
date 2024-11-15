var twist;
var manager;
var ros;
var batterySub;
var cmdVelPub;
var twistIntervalID;
var robot_hostname;
var batterySub;
var startPub;
var startVal;
var startIntervalID;
var sidPub;
var sidVal;
var sidIntervalID;
var isSafeSub;
var isSafeVal = 1;

var systemRebootPub;
var systemShutdownPub;

// var rebootData  = 0;
// var shutdownData = 0;
// var rebootIntervalID;
// var shutdownIntervalID;

var raw_dataSub;
var raw_data_header = " latitude  longitude  x-slope  y-slope  x-temperature y-temperature GPS-msg \r\n";
var raw_data = raw_data_header;
var lineNo = 0;
var maxLine = 20;

var max_linear_speed = 0.5;
var max_angular_speed = 1.2;

var linear_speed = 0.1;
var angular_speed = 0.6;

function initROS() {

    ros = new ROSLIB.Ros({
        url: "ws://" + robot_hostname + ":9090"
    });

    // Init message with zero values.
    twist = new ROSLIB.Message({
        linear: {                                                                   
            x: 0,
            y: 0,
            z: 0
        },
        angular: {
            x: 0,
            y: 0,
            z: 0
        }
    });

    cmdVelPub = new ROSLIB.Topic({
        ros: ros,
        name: '/cmd_vel',
        messageType: 'geometry_msgs/Twist',
        queue_size: 10
    });

    cmdVelPub.advertise();

    systemRebootPub = new ROSLIB.Topic({
        ros: ros,
        name: '/system/reboot',
        messageType: 'std_msgs/Empty'
    });
    systemRebootPub.advertise();

    systemShutdownPub = new ROSLIB.Topic({
        ros: ros,
        name: '/system/shutdown',
        messageType: 'std_msgs/Empty'
    });
    systemShutdownPub.advertise();

    batterySub = new ROSLIB.Topic({
        ros : ros,
        name : '/battery_state',
        messageType : 'sensor_msgs/BatteryState',
        queue_length: 1
    });
    batterySub.subscribe(batteryCallback);

    isSafeSub = new ROSLIB.Topic({
        ros : ros,
        name : '/is_safe',
        messageType : 'std_msgs/Int16',
        queue_length: 1
    })

    isSafeSub.subscribe(isSafeCallback);

    raw_dataSub = new ROSLIB.Topic({
        ros : ros,
        name : '/rover_data',
        messageType : 'std_msgs/String',
        queue_length: 1
    });
    raw_dataSub.subscribe(rawDataCallback);


    startPub = new ROSLIB.Topic({
        ros: ros,
        name: '/start_val',
        messageType: 'std_msgs/Int16',
        queue_size: 10
    });
    startPub.advertise();

    sidPub = new ROSLIB.Topic({
        ros: ros,
        name: '/sidewalk_id',
        messageType: 'std_msgs/String',
        queue_size: 10
    });
    sidPub.advertise();

}

function createJoystick() {

    joystickContainer = document.getElementById('joystick');

    manager = nipplejs.create({
        zone: joystickContainer,
        position: { left: 65 + '%', top: 50 + '%' },
        mode: 'static',
        size: 200,
        color: '#808080',
        restJoystick: true
    });

    manager.on('move', function (evt, nipple) {

        var lin = Math.sin(nipple.angle.radian) * nipple.distance * 0.01;
        var ang = -Math.cos(nipple.angle.radian) * nipple.distance * 0.01;

        twist.linear.x = lin * max_linear_speed;
        twist.angular.z = ang * max_angular_speed;
    });

    manager.on('end', function () {
        twist.linear.x = 0
        twist.angular.z = 0
    });
}

function initTeleopKeyboard() {
    var body = document.getElementsByTagName('body')[0];
    body.addEventListener('keydown', function(e) {
        switch(e.keyCode) {
            case 37: //left
                twist.angular.z = max_angular_speed;
                break;
            case 39: //right
                twist.angular.z = -max_angular_speed;
                break;
            case 38: ///up
                twist.linear.x = max_linear_speed;
                break;
            case 40: //down
                twist.linear.x = -max_linear_speed;
        }
    });
    body.addEventListener('keyup', function(e) {
        switch(e.keyCode) {
            case 37: //left
            case 39: //right
                twist.angular.z = 0;
                break;
            case 38: ///up
            case 40: //down
                twist.linear.x = 0;
        }
    });
}

function batteryCallback(message) {
    var vol = (message.voltage.toPrecision(4)/24)*100;
    if (vol > 100.0){
        vol = 100.0
    }
    // document.getElementById('batteryID').innerHTML = 'Voltage: ' + message.voltage.toPrecision(4) + 'V';
    document.getElementById('batteryID').innerHTML = 'Voltage: ' + vol.toFixed(2) + '% V';
}

function rawDataCallback(message) {
    if(lineNo < maxLine){
        raw_data += message.data + "\r\n";
        lineNo++ ;
    } else {
        raw_data = raw_data_header + message.data + "\r\n";
        lineNo = 1;
    }
    
    document.getElementById('rawdata').value = raw_data;
}

function isSafeCallback(message){
    isSafeVal = message.data;
}

function publishTwist() {
    if(isSaveVal < 1 ){
        twist.linear.x = twist.linear.x * (0.5);
    }
    cmdVelPub.publish(twist);
}

function systemReboot(){
    systemRebootPub.publish()
    alertMessage = "Rebooting system"
    displayAlert(alertMessage)
}

function turnOff(){
    systemShutdownPub.publish()
    alertMessage = "Turning off Rover"
    displayAlert(alertMessage)
}

function publishStart(){
    var startMsg;
    startMsg = new ROSLIB.Message({
        data: startVal
    });
    startPub.publish(startMsg)
}

function checkSID() {
    if(sidVal != undefined) {
        return true
    }
    else{
        return false
    }
}

function setStart(){
    
    if(checkSID()){
        alertMessage = "Started collecting data on SID: " + sidVal + "."
        startVal = 99;
        $(this).prop("disabled",true);
        $(stopButton).prop("disabled",false)
             
    }
    else {
        alertMessage = "Please set SID."
    }
    displayAlert(alertMessage)

}

function setStop(){
    startVal = 0;
    if(checkSID()){
        alertMessage = "Stopped collecting data on SID: " + sidVal + "."
    }
    else {
        alertMessage = "Please set SID."
    }
    displayAlert(alertMessage)

    // enable the start button after STOP is clicked
    $("#stopButton").on("click", function() {
        $(this).prop("disabled", true)
        startButton = document.getElementById("startButton")
        $(startButton).prop("disabled", false);
    });
}

function publishSID(){
    var sidMsg;
    sidMsg = new ROSLIB.Message({
        data: sidVal
    });
    sidPub.publish(sidMsg)
}

function setSID(){
    sidVal = document.getElementById("sid").value;
    if(checkSID()){
        alertMessage = "Sidewalk ID: " + sidVal + " set."
    }
    else{
        alertMessage = "Please enter a sidewalk ID."
    }
    displayAlert(alertMessage)
}

function setSpeed(){
    linear_speed = parseFloat(document.getElementById("speed-select").value);
}

function forward(){
    twist.linear.x = linear_speed;
    twist.angular.z = 0

}

function backward(){
    twist.linear.x = - linear_speed
    twist.angular.z = 0
}

function left(){
    twist.linear.x = 0
    twist.angular.z = linear_speed*1.5
}

function right(){
    twist.linear.x = 0
    twist.angular.z = - linear_speed*1.5
}

function stopRover(){
    twist.linear.x = 0
    twist.angular.z = 0
}

// *** NEEDS WORK ***
// function to check if the SID is set.
    //  this needs some work because it's not checking if it's null


// Function creates and displays a bootstrap alert message for the user. Autofades out after 2.5 seconds
function displayAlert(alertText) {

    // adding the bootstrap alert to the DOM
    var alertsColumn = document.getElementById("alerts")
    
    var alertDiv = document.createElement("div")
    var classATT = "alert alert-primary alert-dismissible fade show"
    var roleATT = "alert"
    alertDiv.setAttribute("class", classATT)
    alertDiv.setAttribute("role", roleATT)
    alertDiv.innerHTML = alertText

    var dismissButton = document.createElement("button")
    dismissButton.setAttribute("type", "button")
    dismissButton.setAttribute("class", "close")
    dismissButton.setAttribute("data-dismiss", "alert")
    dismissButton.setAttribute("aria-label", "Close")

    var spanElement = document.createElement("span")
    spanElement.setAttribute("aria-hidden", "true")
    spanElement.innerHTML = "&times;"

    
    dismissButton.appendChild(spanElement)
    alertDiv.appendChild(dismissButton)

    alertsColumn.appendChild(alertDiv)

    // fading out the alert after 2.5 seconds
    window.setTimeout(function() {
        $(".alert").fadeTo(500, 0).slideUp(500, function(){
            $(this).remove(); 
        });
    }, 2500);
}

window.onblur = function(){  
    twist.linear.x = 0;
    twist.angular.z = 0;
    publishTwist();             
  }  

function shutdown() {
    clearInterval(twistIntervalID);
    cmdVelPub.unadvertise();
    systemRebootPub.unadvertise();
    systemShutdownPub.unadvertise();
    batterySub.unsubscribe();
    raw_dataSub.unsubscribe();
    startPub.unadvertise();
    sidPub.unadvertise();
    ros.close();
}

window.onload = function () {

    
    stopButton = document.getElementById("stopButton")
    $(stopButton).prop("disabled", true);
    

    robot_hostname = location.hostname;

    initROS();
    createJoystick();

    // video = document.getElementById('video');
    // video.src = "http://" + robot_hostname + ":8080/stream?topic=/camera/image_raw&type=ros_compressed";
    
    twistIntervalID = setInterval(() => publishTwist(), 100); // 10 hz
    startIntervalID = setInterval(() => publishStart(), 1000); // 1 hz
    sidIntervalID = setInterval(() => publishSID(), 1000); // 1 hz

    window.addEventListener("beforeunload", () => shutdown());
}


