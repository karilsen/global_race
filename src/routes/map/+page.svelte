<script>
    import { onMount, tick } from "svelte";
    import { browser } from "$app/environment";
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

    // Custom icons – we declare them here and initialize them in onMount after L is available.
    let greenIcon;
    let redIcon;

    // Only use sessionStorage in the browser.
    let totalScore = 0;
    let correctLocations = 0;
    let wrongLocations=0;
  
    if (browser) {
        totalScore = parseInt(sessionStorage.getItem("totalScore")) || 0;
        correctLocations = parseInt(sessionStorage.getItem("correctLocations")) || 0;
        wrongLocations = parseInt(sessionStorage.getItem("wrongLocations")) || 0;
    }

    let score = 1000;
    let timeElapsed = 0;
    let incorrectGuesses = 0;
    let correctMarkers = [];
    let tempMarkers = [];
    let taskReady = false;      // Controls when a task is ready to start
    let taskInProgress = false; // Whether a task is ongoing

    // Define nickname (using sessionStorage/localStorage if available)
    let nickname = "Guest";
    if (browser) {
        nickname = sessionStorage.getItem("nickname") || localStorage.getItem("nickname") || "Guest";
    }

    // Leaderboard
    let leaderboard = [];
    async function fetchLeaderboard() {
        try {
            const response = await fetch("http://localhost:5000/leaderboard");
            leaderboard = await response.json();
        } catch (error) {
            console.error("Error fetching leaderboard:", error);
        }
    }

    async function fetchTask() {
        try {
            const response = await fetch("http://localhost:5000/get_task");
            task = await response.json();
            resetTaskState();

            taskReady = false; // Hide start button once task is loaded
            taskInProgress = true;
            await tick(); // Ensure UI updates before timer starts
            startTimer();
        } catch (error) {
            console.error("Error fetching task:", error);
        }
    }

    function resetTaskState() {
        timeElapsed = 0;
        incorrectGuesses = 0;
        checkMessage = "";
        score = 1000;

        // Remove temporary markers
        tempMarkers.forEach(marker => map.removeLayer(marker));
        tempMarkers = [];

        if (selectedMarker) {
            map.removeLayer(selectedMarker);
        }
    }

    function startTimer() {
    if (taskTimer) {
        clearInterval(taskTimer);
    }
    taskTimer = setInterval(() => {
        timeElapsed++;
        score = Math.max(0, score - 5);
        if (score === 0) {
            stopTimer();
            checkMessage = "Time is up! Revealing correct location...";
            showCorrectLocation();
        }
    }, 1000);
}


    function stopTimer() {
        if (taskTimer) {
            clearInterval(taskTimer);
        }
    }

    // Updated placeMarker function uses custom icons based on the "color" parameter.
    function placeMarker(lat, lon, color, message, permanent = false) {
        // Choose icon based on color parameter.
        let icon;
        if (color === "green") {
            icon = greenIcon;
        } else if (color === "red") {
            icon = redIcon;
        } else {
            icon = L.Icon.Default();
        }

        let marker = L.marker([lat, lon], { icon })
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

        try {
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
                await fetch("http://localhost:5000/update-score", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            nickname,
            points: score,
            correct: true
        })
    });
                saveProgress();
                taskReady = true; // Show "Start Next Task" button
                taskInProgress = false;
                fetchLeaderboard(); // Update leaderboard after score change
            } else {
                incorrectGuesses++;
                placeMarker(playerLat, playerLon, "red", "❌ Wrong guess!");
                score = Math.max(0, score - 100);

                if (incorrectGuesses >= 5 || score <= 0) {
                   
                    stopTimer();
                    checkMessage = "Task forfeited. Revealing correct location...";
                    showCorrectLocation();
                   
                }
            }
        } catch (error) {
            console.error("Error checking task completion:", error);
        }
    }

    function showCorrectLocation() {
        if (!task) return;
        map.setView([task.latitude, task.longitude], 10);
        placeMarker(task.latitude, task.longitude, "red", `❌ Task Failed! Correct location: ${task.location_name}`, true);
        wrongLocations++;
        taskReady = true;
        taskInProgress = false;
    }

    async function startNextTask() {
        if (taskInProgress) return; // Prevent multiple task starts
        taskInProgress = true;
        taskReady = false;
        countdown = 5; // 5-second countdown

        let countdownInterval = setInterval(async () => {
            countdown--;
            await tick(); // Update UI every second
            if (countdown === 0) {
                clearInterval(countdownInterval);
                await fetchTask(); // Fetch new task after countdown
            }
        }, 1000);
    }

    function saveProgress() {
        if (browser) {
            sessionStorage.setItem("totalScore", totalScore);
            sessionStorage.setItem("correctLocations", correctLocations);
        }
    }

    onMount(async () => {
        L = await import("leaflet");

        // Initialize custom icons after Leaflet is available.
        greenIcon = new L.Icon({
            iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-green.png",
            shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.3.1/images/marker-shadow.png",
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowSize: [41, 41]
        });
        redIcon = new L.Icon({
            iconUrl: "https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-red.png",
            shadowUrl: "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.3.1/images/marker-shadow.png",
            iconSize: [25, 41],
            iconAnchor: [12, 41],
            popupAnchor: [1, -34],
            shadowSize: [41, 41]
        });

        map = L.map("map").setView([20, 0], 2);
        L.tileLayer("https://mt1.google.com/vt/lyrs=m&x={x}&y={y}&z={z}", {
            attribution: "&copy; Google Maps",
        }).addTo(map);

        map.on("click", onMapClick);
        taskReady = true; // Show "Start Task" button when the game loads
        fetchLeaderboard();
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
    .progress-bar-container {
        width: 100%;
        background: #e5e7eb; /* Tailwind gray-300 */
        height: 0.75rem;
        border-radius: 0.375rem;
        margin-top: 0.5rem;
    }
    .progress-bar {
        height: 100%;
        background: #10b981; /* Tailwind green-500 */
        border-radius: 0.375rem;
    }
</style>

<!-- UI Layout -->
<div class="flex h-screen gap-6 p-4">
    <!-- Sidebar -->
    <div class="w-80 bg-white shadow-lg p-6 rounded-lg">
        <h2 class="text-2xl font-bold">Player Stats</h2>
        <p class="text-lg">Nickname: {nickname}</p>

        <div class="flex items-center mt-4 space-x-4">
            <div class="w-12 h-12 bg-green-500 text-white flex items-center justify-center rounded-full text-xl font-bold">
                {totalScore}
            </div>
            <p class="text-lg">Total Score</p>
        </div>

        <div class="flex items-center mt-4 space-x-4">
            <div class="w-12 h-12 bg-blue-500 text-white flex items-center justify-center rounded-full text-xl font-bold">
                {correctLocations}
            </div>
            <p class="text-lg">Correct Locations</p>
        </div>

        <div class="flex items-center mt-4 space-x-4">
            <div class="w-12 h-12 bg-red-500 text-white flex items-center justify-center rounded-full text-xl font-bold">
                {wrongLocations}
            </div>
            <p class="text-lg">Wrong Locations</p>
        </div>


        {#if task && !taskReady}
        <div class="mt-4 p-4 bg-white border border-gray-300 rounded-lg shadow-md">
          <div class="flex items-center space-x-2">
            <!-- Icon (example: a location pin icon) -->
            <svg class="w-6 h-6 text-blue-500" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 11c1.657 0 3-1.343 3-3S13.657 5 12 5 9 6.343 9 8s1.343 3 3 3z"></path>
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7z"></path>
            </svg>
            <h3 class="text-xl font-bold text-gray-800">Lets find </h3>
          </div>
          <p class="text-lg mt-2">
        <span class="text-blue-600 font-semibold">{task.location_name}</span>
          </p>
        </div>
      {/if}
      

        <!-- Points Countdown Bar -->
        <div class="mt-4">
            <p class="text-lg">Points Countdown:</p>
            <div class="progress-bar-container">
                <div class="progress-bar" style="width: {score/1000*100}%"></div>
            </div>
            <p class="text-lg text-center mt-1">{score} pts</p>
            <p class="text-lg text-center mt-1">Guess {incorrectGuesses} of 5</p>
        </div>

        {#if taskReady}
            <button on:click={startNextTask} class="mt-4 w-full bg-green-500 text-white py-2 rounded-md hover:bg-green-600">
                Start New Task
            </button>
        {/if}

        {#if task && !taskReady}
            {#if countdown > 0}
                <p class="text-lg text-center mt-2 font-bold text-red-500">Task starts in {countdown}...</p>
            {:else}
                <button on:click={checkTaskCompletion} class="mt-4 w-full bg-blue-500 text-white py-2 rounded-md hover:bg-blue-600">
                    Check if I'm there!
                </button>
            {/if}
            {#if checkMessage}
            <div class="mt-4 mx-auto max-w-md px-4 py-3 bg-red-50 border border-red-400 rounded shadow text-red-700 text-center">
              {checkMessage}
            </div>
          {/if}
        {/if}
    </div>

    <!-- Map -->
    <div class="flex-1">
        <h1 class="text-3xl text-center">Find the Landmark</h1>
        <div id="map" class="w-full h-[85vh] rounded-lg shadow-xl"></div>
    </div>

    <!-- Leaderboard -->
    <div class="w-80 bg-white shadow-lg p-6 rounded-lg">
        <h2 class="text-2xl font-bold">Leaderboard</h2>
        <ul>
            {#each leaderboard as player}
                <li class="flex justify-between py-2 border-b">
                    <span class="font-semibold">{player.nickname}</span>
                    <span>{player.total_score} pts</span>
                </li>
            {/each}
        </ul>
    </div>
</div>
