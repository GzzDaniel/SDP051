console.log("Start of JS script");

//const socket = io("http://32.219.174.238:4000");
const socket = io("https://sdp051car.com");

let arrowPressed = {
    up: false,
    down: false,
    right: false, 
    left: false
};

// _____________ SOCKET IO EVENTS ___________________
socket.on("connect", () => {
    console.log("Connected to server"); 
    socket.emit("userRequestAdd", { message: "ack" });
});

socket.on("connect_error", (error) => {
    if (socket.active) {
      // temporary failure, the socket will automatically try to reconnect
      console.log("reconnecting");
    } else {
      // the connection was denied by the server
      // in that case, `socket.connect()` must be manually called in order to reconnect
      console.log(error.message);
    }
});
// TODO change to false
hasControl = false

socket.on("timestart", (timeAllowed) => {
    //server notifies client start of control time
    //TODO notify client, show text or smthng

    hasControl = true
    console.log("TIMESTART"); 

    let timeleft = timeAllowed; // SECONDS TO CONTROL
    let countdown = setInterval(() => {
        document.getElementById("countdown").textContent = timeleft;
        console.log(`Time left: ${timeleft} seconds`);
        timeleft --;
        socket.emit("timeleft", { message: timeleft })
        if(timeleft < 0){
            hasControl = false
            clearInterval(countdown)
            console.log("timeUp")
            socket.emit("timeover", { message: "ack" })
            document.getElementById("countdown").textContent = "wait";
        }
    }, 1000 )
    
});


// ________________ FUNCTIONS ___________________
// TODO change from string to int for lighter packets
let trottle = '';
let turn = '';

// gets the arrowPressed object and sends the correct input for the PI car
function manageInput(arrowPressed){
    if(arrowPressed.up && !arrowPressed.down){
        throttle = 'forward';
    }
    else if(!arrowPressed.up && arrowPressed.down){
        throttle = 'backward';
    }
    else{
        // UP and DOWN or no button pressed
        throttle = 'stop';
    }
    
    if(arrowPressed.left && !arrowPressed.right){
        turn = 'left';
    }
    else if(!arrowPressed.left && arrowPressed.right){
        turn = 'right';
    }
    else{
        // LEFT and RIGHT or no button pressed
        turn = 'none';
    }

    socket.emit("message", {throttle, turn});
}

// _____________ BUTTON PRESSES LISTENERS _______________________
document.addEventListener("keydown", function(event) {
    if((!event.repeat) && hasControl){
        switch(event.key) {
            case "ArrowUp":
                console.log("Up arrow pressed");
                //socket.emit("message", "UP pressed")
                arrowPressed.up = true;
                break;
            case "ArrowDown":
                console.log("Down arrow pressed");
                //socket.emit("message", "DOWN pressed")
                arrowPressed.down = true;
                break;
            case "ArrowLeft":
                console.log("Left arrow pressed");
                //socket.emit("message", "LEFT pressed")
                arrowPressed.left = true;
                break;
            case "ArrowRight":
                console.log("Right arrow pressed");
                //socket.emit("message", "RIGHT pressed")
                arrowPressed.right = true;
                break;
        }
        console.log(arrowPressed.up, arrowPressed.down, arrowPressed.left, arrowPressed.right);
        manageInput(arrowPressed);
    }
});

document.addEventListener("keyup", function(event) {
    if(hasControl){
        switch(event.key) {
            case "ArrowUp":
                console.log("Up arrow released");
                //socket.emit("message", "UP released")
                arrowPressed.up = false;
                break;
            case "ArrowDown":
                console.log("Down arrow released");
                //socket.emit("message", "DOWN released")
                arrowPressed.down = false;
                break;
            case "ArrowLeft":
                console.log("Left arrow released");
                //socket.emit("message", "LEFT released")
                arrowPressed.left = false;
                break;
            case "ArrowRight":
                console.log("Right arrow released");
                //socket.emit("message", "RIGHT released")
                arrowPressed.right = false
                break;
        }
        console.log(arrowPressed.up, arrowPressed.down, arrowPressed.left, arrowPressed.right);
        manageInput(arrowPressed);
    }
});


// __________________ VIRTUAL CONTROLLER ____________________
document.addEventListener("DOMContentLoaded", function() {
    console.log("JS Loaded");

    
    //Get the button and slider from the html
    const buttonUp = document.getElementById("forward");
    const buttonDown = document.getElementById("backward");
    const buttonLeft = document.getElementById("left");
    const buttonRight = document.getElementById("right");
    const slider = document.getElementById("slider");
    const sliderValue = document.getElementById("sliderValue");

    //Receive the value of the slider and send to the PI(Speed).
    slider.addEventListener("input",function(){
        const speed = slider.value;
        //sliderValue.textContent = speed;
        
        console.log("Sending speed:", speed);
        socket.emit("message", { throttle: speed, turn: "none" });
    })

    // TOUCH PRESSES
    buttonUp.addEventListener("touchstart", function() {
        console.log("Forward button clicked");
        //socket.emit("message", { throttle: "forward", turn: "none" });
        arrowPressed.up = true;
        manageInput(arrowPressed);
    });

    buttonDown.addEventListener("touchstart", function() {
        console.log("Backward button clicked");
        //socket.emit("message", { throttle: "backward", turn: "none" });
        arrowPressed.down = true;
        manageInput(arrowPressed);
    });

    buttonLeft.addEventListener("touchstart", function() {
        console.log("Left button clicked");
        //socket.emit("message", { throttle: "stop", turn: "left" });
        arrowPressed.left = true;
        manageInput(arrowPressed);
    });

    buttonRight.addEventListener("touchstart", function() {
        console.log("Right button clicked");
        //socket.emit("message", { throttle: "stop", turn: "right" });
        arrowPressed.right = true;
        manageInput(arrowPressed);
    });

    // TOUCH RELEASES
    buttonUp.addEventListener("touchend", function() {
        console.log("Forward button released");
        //socket.emit("message", { throttle: "forward", turn: "none" });
        arrowPressed.up = false;
        manageInput(arrowPressed);
    });

    buttonDown.addEventListener("touchend", function() {
        console.log("Backward button released");
        //socket.emit("message", { throttle: "backward", turn: "none" });
        arrowPressed.down = false;
        manageInput(arrowPressed);
    });

    buttonLeft.addEventListener("touchend", function() {
        console.log("Left button release");
        //socket.emit("message", { throttle: "stop", turn: "left" });
        arrowPressed.left = false;
        manageInput(arrowPressed);
    });

    buttonRight.addEventListener("touchend", function() {
        console.log("Right button released");
        //socket.emit("message", { throttle: "stop", turn: "right" });
        arrowPressed.right = false;
        manageInput(arrowPressed);
    });

});
    

