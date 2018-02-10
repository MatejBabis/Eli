// TODO: BEAUTIFY

// Check if browser is Chromium based
// from https://stackoverflow.com/a/13348618
function isChrome() {
  var isChromium = window.chrome,
    winNav = window.navigator,
    vendorName = winNav.vendor,
    isOpera = winNav.userAgent.indexOf("OPR") > -1,
    isIEedge = winNav.userAgent.indexOf("Edge") > -1,
    isIOSChrome = winNav.userAgent.match("CriOS");

  if (isIOSChrome) {
    return true;
  } else if (
    isChromium !== null &&
    typeof isChromium !== "undefined" &&
    vendorName === "Google Inc." &&
    isOpera === false &&
    isIEedge === false
  ) {
    return true;
  } else {
    return false;
  }
}

// This is the core function that handles user input
// TODO: BREAK INTO SEPARATE FUNCTIONS
function handleInput(userText, dialogflowClient) {
  if (playingStage && (userText == "next" || userText == "stop" || userText == "skip")) {
    userSays(userText);
    ga('send', 'event', 'Message', 'add', 'user');
    // stop the currently playing audio
    $('.plyr--playing').children()[0].pause();
  } else if (playingStage) {
    //
    // ignore any other input while tracks are playing
    //
  } else {
    userSays(userText);
    ga('send', 'event', 'Message', 'add', 'user');

    // Dialogflow starts here
    // roughly based on https://jaanus.com/api-ai-voicebot/
    let promise = dialogflowClient.textRequest(userText);
    promise
      .then(handleResponse)
      .catch(handleError);

    function handleResponse(serverResponse) {
      // say the response
      var speech = serverResponse["result"]["fulfillment"]["speech"];
      var msg = new SpeechSynthesisUtterance(speech);
      botSays(speech);

      ga('send', 'event', 'Message', 'add', 'bot');
      window.speechSynthesis.speak(msg);

      response = serverResponse["result"]["action"];

      // Give me two songs
      if (response == "preferenceElicitation") {
        var metadata = serverResponse["result"]["fulfillment"]["data"];

        var t1_desc = metadata[0][0];
        var t1_url = metadata[0][1];
        var t2_desc = metadata[1][0];
        var t2_url = metadata[1][1];

        msg.onend = function() {
          playSong(t1_desc, t1_url).then(function() {
            playSong(t2_desc, t2_url).then(function() {
              playingStage = false;
              var question = "Which one did you like better?";
              msg = new SpeechSynthesisUtterance(question);
              botSays(question);
              window.speechSynthesis.speak(msg);
            })
          })
        }
        // Repeat a song
      } else if (response == "preferenceElicitation.repeat") {
        var choice = serverResponse["result"]["fulfillment"]["data"];
        if (choice != null) {
          msg.onend = function() {
            replaySong(choice).then(function() {
              playingStage = false;
              var question = "Which one did you like better?";
              msg = new SpeechSynthesisUtterance(question);
              botSays(question);
              window.speechSynthesis.speak(msg);
            })
          }
        }
      }
    }

    function handleError(serverError) {
      console.log("Error from api.ai server: ", serverError);
      // TODO: PROBABLY SOME RESPONSE
    }
  }
}

// #######################
// #  H E L P E R S      #
// #######################

function scrollDown() {
  var conv = document.querySelector('#conversation');
  conv.scrollTop = conv.scrollHeight - conv.clientHeight;
}

// Toggle between microphone state
function micActive() {
  $("#start").css("background-color", "rgb(87,196,255)");
  $("#start").css("animation", "pulse-active 2s infinite");
}

function micInactive() {
  $("#start").css("background-color", "rgb(207,207,213)");
  $("#start").css("animation", "")
}

function botSays(text) {
  $("#conversation").append('<div class="bot speech-bubble"><p>' + text + '</p></div>');
  scrollDown();
}

function userSays(text) {
  $("#conversation").append('<div class="user speech-bubble"><p>' + text + '</p></div>');
  scrollDown();
}

function addSong(url) {
  $("#conversation").append('<div class="bot speech-bubble"><audio controls><source src="' + url + '" type="audio/mpeg"></audio></div>');
  plyr.setup($("audio:last").get(0), {
    controls: ['play', 'current-time', 'mute'],
    autoplay: true
  });
  scrollDown();
}

var playingStage = false;

function playSong(desc, url) {
  return new Promise(function(resolve, reject) { // return a promise
    playingStage = true;
    botSays(desc);
    addSong(url);
    $('audio:last').get(0).preload = "auto"; // intend to play through
    $("audio:last").on('ended pause', resolve);
  });
}

function replaySong(audioElemIndex) {
  return new Promise(function(resolve, reject) { // return a promise
    // find all audio elemets
    var audioElements = $('audio');
    var songsDisplayed = audioElements.length;
    // get the index position
    var songPos = songsDisplayed - 2 + audioElemIndex;
    // replay the song
    var track = audioElements[songPos];
    track.currentTime = 0;
    track.play();
    playingStage = true;
    $(track).on('ended pause', resolve);
  });
}

// #######################
// #  M A I N   F U N C  #
// #######################

document.addEventListener("DOMContentLoaded", function(event) {

  // check for compatibility
  if ((!isChrome()) || (!('speechSynthesis' in window)) || (!('webkitSpeechRecognition' in window))) {
    alert("This browser is incompatible.")
    window.location.replace("/blank");
    return;
  }

  // Dialogflow client
  const apiClient = new ApiAi.ApiAiClient({
    accessToken: '723e3f6e567d4260b6b93b4ad40a8783'
  });

  // Welcome message
  botSays("Hi! I’m Eli.");

  var recognition = new webkitSpeechRecognition();
  var recognizedText = null;
  var recording = null;
  recognition.continuous = false;

  recognition.onstart = function() {
    recognizedText = null;
    recording = true;
  };

  // Human input was received
  // MAIN BIT
  recognition.onresult = function(ev) {
    // For continuous speech, the results come as a list
    var lastResult = ev.results.length - 1;
    recognizedText = ev["results"][lastResult][0]["transcript"];

    handleInput(recognizedText, apiClient);
  };

  recognition.onerror = function(ev) {
    console.log("Speech recognition error", ev);
    // TODO: PROBABLY SOME RESPONSE
  };

  // Listner for microphone button click
  $("#start").on("click", function(ev) {
    if (!recording) {
      ga('send', 'event', 'Button', 'click');
      micActive();
      recognition.start();
      ev.preventDefault();
      recording = true;
    } else {
      // If user wishes to stop recording
      console.log("aborted");
      recognition.abort();
    }
  });

  recognition.onend = function() {
    micInactive();
    recording = false;
  };

  // Handles text input
  $("#textInput").keypress(function(event) {
    if (event.which == 13) {
      event.preventDefault();
      var textInput = $("#textInput").val();
      // Empty the field
      $("#textInput").val("");
      $("#textInput").blur();
      // Don't send an empty query
      if (textInput.length > 0) {
        handleInput(textInput, apiClient);
      }
    }
  });
});
