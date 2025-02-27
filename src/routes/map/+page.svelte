<script>
    import { onMount, tick } from "svelte";
    import "leaflet/dist/leaflet.css";
  
    let map;
    let task = null;
    let playerLat = null;
    let playerLon = null;
    let checkMessage = "";
    let selectedMarker = null;
    let countdown = 0;
    let taskTimer = null;
    let L;
  
    // Game state variables (stored in sessionStorage)
    let totalScore = parseInt(sessionStorage.getItem("totalScore")) || 0;
    let correctLocations = parseInt(sessionStorage.getItem("correctLocations")) || 0;
    let score = 1000;
    let timeElapsed = 0;
    let incorrectGuesses = 0;
    let correctMarkers = [];
    let tempMarkers = [];
    let taskReady = false; // ✅ Controls when a task is ready to start
    let taskInProgress = false; // ✅ Ensure it is defined properly

  
    async function fetchTask() {
    const response = await fetch("http://localhost:5000/get_task");
    task = await response.json();
    resetTaskState();

    taskReady = false; // ✅ Hide "Start Task" button after task loads
    taskInProgress = true; // ✅ Ensure task is in progress

    await tick(); // ✅ Ensures UI updates before starting the timer
    startTimer(); // ✅ Start the task timer AFTER loading the new task
}



  
    function resetTaskState() {
      timeElapsed = 0;
      incorrectGuesses = 0;
      checkMessage = "";
      score = 1000;
  
      tempMarkers.forEach(marker => map.removeLayer(marker));
      tempMarkers = [];
  
      if (selectedMarker) {
        map.removeLayer(selectedMarker);
      }
    }
  
    function startCountdown() {
      countdown = 5;
      let countdownInterval = setInterval(() => {
        countdown--;
        if (countdown === 0) {
          clearInterval(countdownInterval);
          startTimer();
        }
      }, 1000);
    }
  
    function startTimer() {
      if (taskTimer) {
        clearInterval(taskTimer);
      }
      taskTimer = setInterval(() => {
        timeElapsed++;
        score = Math.max(0, score - 5);
      }, 1000);
    }
  
    function stopTimer() {
      if (taskTimer) {
        clearInterval(taskTimer);
      }
    }
  
    function placeMarker(lat, lon, color, message, permanent = false) {
      let marker = L.marker([lat, lon], { color })
        .addTo(map)
        .bindPopup(message)
        .openPopup();
  
      if (permanent) {
        correctMarkers.push(marker);
      } else {
        tempMarkers.push(marker);
      }
    }
  
    function onMapClick(event) {
      if (selectedMarker) {
        map.removeLayer(selectedMarker);
      }
      playerLat = event.latlng.lat;
      playerLon = event.latlng.lng;
      selectedMarker = L.marker([playerLat, playerLon])
        .addTo(map)
        .bindPopup("You selected this location")
        .openPopup();
    }
  
    async function checkTaskCompletion() {
    if (!task || playerLat === null || playerLon === null) {
        checkMessage = "Click on the map to select a location first!";
        return;
    }

    const response = await fetch("http://localhost:5000/check-task", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            latitude: playerLat,
            longitude: playerLon,
            task_name: task.location_name,
        }),
    });

    const result = await response.json();
    checkMessage = result.message;

    if (result.success) {
        stopTimer();
        placeMarker(playerLat, playerLon, "green", "✔ Correct!", true);
        correctLocations++;
        totalScore += score;
        saveProgress();
        taskReady = true; // ✅ Show "Start Next Task" button
        taskInProgress = false; // ✅ Reset task state
    } else {
        incorrectGuesses++;
        placeMarker(playerLat, playerLon, "red", "❌ Wrong guess!");
        score = Math.max(0, score - 100);

        if (incorrectGuesses >= 5) {
            stopTimer();
            checkMessage = "Task forfeited. Revealing correct location...";
            showCorrectLocation();
        }
    }
}

  
    function showCorrectLocation() {
      if (!task) return;
      map.setView([task.latitude, task.longitude], 10);
      placeMarker(task.latitude, task.longitude, "red", `❌ Task Failed! Correct location: ${task.location_name}`, true);
      taskReady = true; // ✅ Show "Start Next Task" button
    }
  
    function startNextTask() {
    if (taskInProgress) return; // ✅ Prevent multiple starts
    taskInProgress = true; // ✅ Mark the task as in progress
    taskReady = false; // ✅ Hide the "Start Task" button
    countdown = 5; // ✅ Set countdown to 5 seconds

    let countdownInterval = setInterval(() => {
        countdown--;
        if (countdown === 0) {
            clearInterval(countdownInterval);
            fetchTask(); // ✅ Fetch the new task after countdown
        }
    }, 1000);
}




  
    function saveProgress() {
      sessionStorage.setItem("totalScore", totalScore);
      sessionStorage.setItem("correctLocations", correctLocations);
    }
  
    onMount(async () => {
    L = await import("leaflet");

    map = L.map("map").setView([20, 0], 2);

    L.tileLayer("https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}", {
    attribution: "&copy; Google Maps",
}).addTo(map);



    map.on("click", onMapClick);

    taskReady = true; // ✅ Show "Start Task" button when the game loads
});

  </script>
  
  <style>
    .sidebar {
      position: fixed;
      left: 10px;
      top: 50px;
      width: 250px;
      background: white;
      padding: 15px;
      border-radius: 10px;
      box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
    }
  </style>
  
  <div class="container mx-auto mt-8 flex">
    <!-- Sidebar -->
    <div class="sidebar">
      <h2 class="text-xl font-bold">Game Stats</h2>
      <p><strong>Total Score:</strong> {totalScore}</p>
      <p><strong>Current Score:</strong> {score}</p>
      <p><strong>Correct Locations:</strong> {correctLocations}</p>
      <p><strong>Time:</strong> {timeElapsed} sec</p>
      <p><strong>Attempts Left:</strong> {5 - incorrectGuesses}</p>
    </div>
  
    <!-- Game Map & Controls -->
    <div class="flex-1">
      <h1 class="text-3xl font-bold text-center mb-4">Find the Landmark</h1>
  
      <div class="mb-6 text-center">
        {#if taskReady}
            <button on:click={startNextTask} class="bg-green-500 text-white px-4 py-2 rounded-md mt-4 hover:bg-green-600">
                Start Task
            </button>
        {/if}
    
        {#if task && !taskReady}
            <p class="text-lg font-semibold">
                Your task: Find <span class="text-blue-600">{task.location_name}</span> on the map!
            </p>
            {#if countdown > 0}
                <p class="text-red-500 text-lg font-bold">Task starting in {countdown}...</p>
            {:else}
                <button on:click={checkTaskCompletion} class="bg-blue-500 text-white px-4 py-2 rounded-md mt-4 hover:bg-blue-600">
                    Check if I'm there!
                </button>
            {/if}
            <p class="text-lg font-semibold text-red-500 mt-2">{checkMessage}</p>
        {/if}
    </div>
    
  
      <div id="map" class="w-full h-[750px] rounded-lg shadow-md"></div>
    </div>
  </div>
  