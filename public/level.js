
const AIM_POWER_SPEED = 0.1;
const SNOWBALL_COLLECT_TIME = 2000;

var time;
var snowballCollectionStartTime;
var snowballCollectionPercentage; // is between 0-1

var map;
var layer;

// map of the player names mapped to their position, 
// health and sprite.
// Does not include this client's player
// name -> {x, y, health, sprite}
var players = {};

// List of all the players' names
var playerNames = [];

var mainPlayerPosition;
var mainPlayerHealth;
var mainPlayerSprite;
var mainPlayerName;

var numSnowballs;
var formingSnowball;

var aiming;
var currentForce;
var currentAngle;
var aimCounter;
var aimSprite;
var powerBar;

function initLevel() {
    aiming = false;
    currentForce = 0;
    aimCounter = 0;
    numSnowballs = 0;
    formingSnowball = false;
    snowballCollectionStartTime = 0;
    snowballCollectionPercentage = 0;

    time = new Date().getTime();
    game.stage.backgroundColor = '#909090';
    
    map = game.add.tilemap('snowballMap');
    map.addTilesetImage('tileset', 'tileset');
    
    layer = map.createLayer('mapLayer');
    layer.resizeWorld();

    mainPlayerPosition = {x: 300, y: 300};
    mainPlayerHealth = 100;
    mainPlayerSprite = game.add.sprite(
        mainPlayerPosition.x,
        mainPlayerPosition.y,
        'snowman'
    );
    
    powerBar = game.add.sprite(10, 110, 'powerbar');

    for (var i in playerNames) {
        var name = playerNames[i];
        if (name != mainPlayerName) {
            sprite = game.add.sprite(0, 0, 'snowman');
            players[name] = {x: 0, y: 0, health: 0, sprite: sprite};
        }
        else {
            aimSprite = game.add.sprite(100, 100, 'arrow');
            aimSprite.anchor.setTo(0,0.5);
        }
    }
}

function updatePlayerPosition(name, x, y) {
    if (name == mainPlayerName) {
        mainPlayerPosition.x = x;
        mainPlayerPosition.y = y;
        mainPlayerSprite.x = x;
        mainPlayerSprite.y = y;
        aimSprite.x = mainPlayerPosition.x + mainPlayerSprite.width/2;
        aimSprite.y = mainPlayerPosition.y + 5;
        aimSprite.angle = currentAngle * 180/Math.PI;
    } else {
        var p = players[name];
        p.x = x;
        p.y = y;
        p.sprite.x = x;
        p.sprite.y = y;
    }
}

function updatePowerBar() {
    powerBar.scale.y = -currentForce * 100;
    powerBar.tint = rgb2hex(255*currentForce, 50*(1 - currentForce) + 205, 0);
}

function rgb2hex(red, green, blue) {
    var rgb = blue | (green << 8) | (red << 16);
    return rgb;
}

function addPlayers(playerList) {
    playerNames = playerList;
}

function getAngle(x1, y1, x2, y2) {
    return Math.atan2((y2 - y1),(x2 - x1));
}

function getCurrentTime() {
    return (new Date()).getTime();
}

function handleSnowballForming() {
    if (isFormSnowballPressed()) {
        // start timer
        if (!formingSnowball) {
            snowballCollectionStartTime = getCurrentTime();
            snowballCollectionPercentage = 0;
            formingSnowball = true;
        }

        var timeDiff = 
            getCurrentTime() - snowballCollectionStartTime;

        if (timeDiff >= SNOWBALL_COLLECT_TIME) {
            // New ball is complete, stash it
            numSnowballs++;
            sendNewSnowball();
            formingSnowball = false;
            snowballCollectionPercentage = 0;
            console.log("NEW SNOWBALL");
        } else {
            snowballCollectionPercentage = timeDiff / SNOWBALL_COLLECT_TIME;
        }

    } else {
        formingSnowball = false;
        snowballCollectionPercentage = 0;
    }
    console.log(snowballCollectionPercentage);
}

function levelUpdate() {
    var newTime = getCurrentTime();
    var deltaTime = (newTime - time)/30;
    time = newTime;
    
    if (isLeftMouseButtonPressed()) {
        aiming = true;
        currentForce = (-Math.cos(
                aimCounter*AIM_POWER_SPEED) + 1)/2;
        currentAngle = getAngle(mainPlayerPosition.x,
                    mainPlayerPosition.y, 
                    getMouseX(), getMouseY());
                    
        updatePowerBar();
        console.log(currentAngle);
        aimCounter++;
    } else {
        if (aiming) {
            sendFire(currentAngle, currentForce);
        }
        currentForce = 0;
        aiming = false;
        aimCounter = 0;
    }
    handleSnowballForming();
}

