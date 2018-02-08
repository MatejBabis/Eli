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

function scrollDown() {
  var conv = document.querySelector('#conversation');
  conv.scrollTop = conv.scrollHeight - conv.clientHeight;
}

// Toggle between microphone state
function micActive() {
  var event = jQuery.Event("listening");
  $("#start").trigger(event);

  $("#start").css("background-color", "rgb(87,196,255)");
  $("#start").css("animation", "pulse-active 2s infinite");
  $(this).one("click", micInactive);
}

function micInactive() {
  var event = jQuery.Event("not-listening");
  $("#start").trigger(event);

  $("#start").css("background-color", "rgb(207,207,213)");
  $("#start").css("animation", "")
  $(this).one("click", micActive);
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

function playSong(desc, url) {
  return new Promise(function(resolve, reject) { // return a promise
    botSays(desc);
    addSong(url);
    $('audio:last').get(0).preload = "auto"; // intend to play through
    $("audio:last").on('ended pause', resolve);
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
  recognition.continuous = true;

  recognition.onstart = function() {
    recognizedText = null;
  };

  // Human input was received
  recognition.onresult = function(ev) {
    // For continuous speech, the results come as a list
    var lastResult = ev.results.length - 1;
    recognizedText = ev["results"][lastResult][0]["transcript"];

    userSays(recognizedText);
    ga('send', 'event', 'Message', 'add', 'user');

    // Dialogflow starts here
    // roughly based on https://jaanus.com/api-ai-voicebot/
    let promise = apiClient.textRequest(recognizedText);
    promise
      .then(handleResponse)
      .catch(handleError);

    function handleResponse(serverResponse) {

      if (serverResponse["result"]["action"] == "preferenceElicitation") {
        var metadata = serverResponse["result"]["fulfillment"]["data"];
        var speech = serverResponse["result"]["fulfillment"]["speech"];

        var t1_desc = metadata[0][0];
        var t1_url = metadata[0][1];
        var t2_desc = metadata[1][0];
        var t2_url = metadata[1][1];

        var msg = new SpeechSynthesisUtterance(speech);
        botSays(speech);

        ga('send', 'event', 'Message', 'add', 'bot');

        window.speechSynthesis.speak(msg);

        // FIXME: FIRST COMPARISON TRACKS SOMETIMES WON'T GET ADDED

        msg.onend = function() {
          playSong(t1_desc, t1_url).then(function() {
            playSong(t2_desc, t2_url).then(function() {
              var question = "Which one did you like better?";
              msg = new SpeechSynthesisUtterance(question);
              botSays(question);
              window.speechSynthesis.speak(msg);
            })
          })
        }
      } else {
        var speech = serverResponse["result"]["fulfillment"]["speech"];

        var msg = new SpeechSynthesisUtterance(speech);
        botSays(speech);

        ga('send', 'event', 'Message', 'add', 'bot');

        window.speechSynthesis.speak(msg);
      }
    }

    function handleError(serverError) {
      console.log("Error from api.ai server: ", serverError);
      // TODO: PROBABLY SOME RESPONSE
    }
  };

  recognition.onerror = function(ev) {
    console.log("Speech recognition error", ev);
    // TODO: PROBABLY SOME RESPONSE
  };

  // Listner for microphone button click
  $("#start").one("click", micActive);

  // If user wishes to start recording
  $("#start").on("listening", function(ev) {
    ga('send', 'event', 'Button', 'click');
    recognition.start();
    ev.preventDefault();
  });

  // If user wishes to stop recording
  $("#start").on("not-listening", function() {
    recognition.stop();
  });
});
