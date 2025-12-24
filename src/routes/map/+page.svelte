<script>
    import { onMount } from "svelte";
    import { browser } from "$app/environment";
    import { goto } from "$app/navigation";
    import "leaflet/dist/leaflet.css";

    const MAX_GUESSES = 5;
    const AUTO_NEXT_DELAY = 2000; // ms before automatically loading the next task

    let map;
    let L;
    let permanentLayer;
    let greenIcon;
    let redIcon;

    let task = null;
    let playerLat = null;
    let playerLon = null;
    let selectedMarker = null;
    let tempMarkers = [];
    let correctMarkers = [];

    let taskTimer = null;
    let nextTaskTimeout = null;

    let gameStarted = false;
    let taskInProgress = false;
    let loadingTask = false;

    let totalScore = 0;
    let correctLocations = 0;
    let wrongLocations = 0;
    let score = 1000;
    let timeElapsed = 0;
    let incorrectGuesses = 0;
    let checkMessage = "";
    let checkStatus = null;      // "success" | "fail" | null
    let lastBonusPoints = 0;
    let lastDistanceKm = null;
    let leaderboard = [];
    let nickname = "Guest";

    onMount(async () => {
        if (!browser) return;

        const savedNickname = sessionStorage.getItem("nickname") || localStorage.getItem("nickname");
        if (!savedNickname) {
            goto("/");
            return;
        }

        nickname = savedNickname;
        totalScore = parseInt(sessionStorage.getItem("totalScore")) || 0;
        correctLocations = parseInt(sessionStorage.getItem("correctLocations")) || 0;
        wrongLocations = parseInt(sessionStorage.getItem("wrongLocations")) || 0;

        await setupMap();
        fetchLeaderboard();
    });

    async function setupMap() {
        if (map) return;
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

        // Create the permanent layer group for markers and add it to the map.
        permanentLayer = L.layerGroup().addTo(map);

        map.on("click", onMapClick);
    }

    function stopTimer() {
        if (taskTimer) {
            clearInterval(taskTimer);
        }
    }

    function startTimer() {
        stopTimer();
        taskTimer = setInterval(() => {
            timeElapsed++;
            score = Math.max(0, score - 5);
            if (score === 0) {
                handleTimeout();
            }
        }, 1000);
    }

    function resetTaskState() {
        timeElapsed = 0;
        incorrectGuesses = 0;
        checkMessage = "";
        checkStatus = null;
        lastBonusPoints = 0;
        lastDistanceKm = null;
        score = 1000;
        playerLat = null;
        playerLon = null;

        tempMarkers.forEach(marker => map.removeLayer(marker));
        tempMarkers = [];

        if (selectedMarker) {
            map.removeLayer(selectedMarker);
            selectedMarker = null;
        }
    }

    function onMapClick(event) {
        if (!taskInProgress) return;
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

    function placeMarker(lat, lon, color, message, permanent = false) {
        let icon;
        if (color === "green") {
            icon = greenIcon;
        } else if (color === "red") {
            icon = redIcon;
        } else {
            icon = L.Icon.Default();
        }

        const marker = L.marker([lat, lon], { icon })
            .bindPopup(message)
            .openPopup();

        if (permanent) {
            marker.addTo(permanentLayer);
            correctMarkers.push(marker);
        } else {
            marker.addTo(map);
            tempMarkers.push(marker);
        }
    }

    async function fetchLeaderboard() {
        try {
            const response = await fetch("http://localhost:5000/leaderboard");
            leaderboard = await response.json();
        } catch (error) {
            console.error("Error fetching leaderboard:", error);
        }
    }

    async function fetchTask() {
        const response = await fetch("http://localhost:5000/get_task");
        task = await response.json();
    }

    async function startGame() {
        if (gameStarted || loadingTask) return;
        gameStarted = true;
        await startNextTask();
    }

    function queueNextTask() {
        if (!gameStarted) return;
        if (nextTaskTimeout) {
            clearTimeout(nextTaskTimeout);
        }
        nextTaskTimeout = setTimeout(() => {
            startNextTask();
        }, AUTO_NEXT_DELAY);
    }

    async function startNextTask() {
        if (loadingTask) return;
        loadingTask = true;
        stopTimer();
        resetTaskState();
        try {
            await fetchTask();
            taskInProgress = true;
            startTimer();
        } catch (error) {
            checkStatus = "fail";
            checkMessage = "Could not load a task. Please try again.";
            taskInProgress = false;
        } finally {
            loadingTask = false;
        }
    }

    async function applyScore(points, bonusPoints) {
        const payload = {
            nickname,
            points: Math.max(points, 0),
            bonus_points: Math.max(bonusPoints, 0),
            correct: true
        };
        try {
            const response = await fetch("http://localhost:5000/update-score", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload),
            });
            const result = await response.json();
            if (response.ok) {
                totalScore = result.total_score;
                correctLocations = result.correct_locations;
            } else {
                totalScore += payload.points + payload.bonus_points;
                correctLocations += 1;
            }
        } catch (error) {
            console.error("Error updating score:", error);
            totalScore += payload.points + payload.bonus_points;
            correctLocations += 1;
        }
        saveProgress();
        fetchLeaderboard();
    }

    async function checkTaskCompletion() {
        if (!taskInProgress || !task) {
            checkMessage = "Start the task first.";
            checkStatus = "fail";
            return;
        }
        if (playerLat === null || playerLon === null) {
            checkMessage = "Click on the map to select a location first!";
            checkStatus = "fail";
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
            checkStatus = result.success ? "success" : "fail";
            lastBonusPoints = Number(result.bonus_points) || 0;
            lastDistanceKm = typeof result.distance_km === "number" ? result.distance_km : null;
            const distanceText = lastDistanceKm !== null ? `${lastDistanceKm.toFixed(2)} km` : "unknown distance";
            checkMessage = result.message || (result.success ? `Task completed! Distance: ${distanceText}` : `Not close enough. Distance: ${distanceText}`);

            if (result.success) {
                stopTimer();
                await applyScore(score, lastBonusPoints);
                placeMarker(task.latitude, task.longitude, "green", `Correct! Distance: ${distanceText}`, true);
                taskInProgress = false;
                queueNextTask();
            } else {
                incorrectGuesses++;
                placeMarker(playerLat, playerLon, "red", "Wrong guess!");
                score = Math.max(0, score - 100);

                if (incorrectGuesses >= MAX_GUESSES) {
                    failRound(`Max guesses reached. Correct location: ${task.location_name}`);
                }
            }
        } catch (error) {
            console.error("Error checking task completion:", error);
            checkStatus = "fail";
            checkMessage = "Could not check task right now. Please try again.";
        }
    }

    function handleTimeout() {
        stopTimer();
        failRound("Time is up. Correct location shown.");
    }

    function failRound(message) {
        if (!task) return;
        stopTimer();
        checkStatus = "fail";
        checkMessage = message || `Task failed. Correct location: ${task.location_name}`;
        placeMarker(task.latitude, task.longitude, "red", `Correct location: ${task.location_name}`, true);
        wrongLocations++;
        saveProgress();
        taskInProgress = false;
        queueNextTask();
    }

    function saveProgress() {
        if (browser) {
            sessionStorage.setItem("totalScore", totalScore);
            sessionStorage.setItem("correctLocations", correctLocations);
            sessionStorage.setItem("wrongLocations", wrongLocations);
        }
    }

    function endSession() {
        stopTimer();
        if (nextTaskTimeout) {
            clearTimeout(nextTaskTimeout);
        }
        taskInProgress = false;
        gameStarted = false;
        if (browser) {
            sessionStorage.clear();
            localStorage.removeItem("nickname");
        }
        goto("/");
    }
</script>

<style>
    .progress-bar-container {
        width: 100%;
        background: #e5e7eb;
        height: 0.75rem;
        border-radius: 0.375rem;
        margin-top: 0.5rem;
    }
    .progress-bar {
        height: 100%;
        background: #10b981;
        border-radius: 0.375rem;
    }
</style>

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

        <div class="mt-4">
            <p class="text-lg">Points Countdown:</p>
            <div class="progress-bar-container">
                <div class="progress-bar" style={`width: ${score / 1000 * 100}%`}></div>
            </div>
            <p class="text-lg text-center mt-1">{score} pts</p>
            <p class="text-lg text-center mt-1">Guess {incorrectGuesses} of {MAX_GUESSES}</p>
        </div>

        {#if task}
            <div class="mt-4 p-4 bg-white border border-gray-200 rounded-lg shadow">
                <p class="text-sm text-gray-500">Current quest</p>
                <p class="text-lg font-semibold text-gray-800">{task.location_name}</p>
                <p class="text-xs text-gray-500 mt-1">
                    {#if taskInProgress}
                        Select on the map, then check your answer.
                    {:else if gameStarted}
                        Preparing next round...
                    {:else}
                        Press start to begin.
                    {/if}
                </p>
                {#if taskInProgress}
                    <button on:click={checkTaskCompletion} class="mt-3 w-full bg-blue-500 text-white py-2 rounded-md hover:bg-blue-600">
                        Check if I'm there!
                    </button>
                {/if}
            </div>
        {/if}

        {#if checkMessage}
            <div class={`mt-4 mx-auto max-w-md px-4 py-3 rounded shadow text-center border ${checkStatus === "success" ? "bg-green-50 border-green-400 text-green-800" : "bg-red-50 border-red-400 text-red-700"}`}>
                <p class="font-semibold">{checkMessage}</p>
                {#if checkStatus === "success" && lastBonusPoints}
                    <p class="text-sm mt-1">Bonus: {lastBonusPoints} pts</p>
                {/if}
                {#if lastDistanceKm !== null}
                    <p class="text-sm mt-1">Distance: {lastDistanceKm.toFixed(2)} km</p>
                {/if}
            </div>
        {/if}

        <div class="mt-4 space-y-2">
            {#if !gameStarted}
                <button on:click={startGame} class="w-full bg-green-500 text-white py-2 rounded-md hover:bg-green-600">
                    Start Task
                </button>
            {:else}
                <p class="text-sm text-gray-600">{taskInProgress ? "Round in progress" : "Next round loading..."}</p>
                <button on:click={endSession} class="w-full bg-gray-200 text-gray-800 py-2 rounded-md hover:bg-gray-300">
                    End Session
                </button>
            {/if}
        </div>
    </div>

    <!-- Map -->
    <div class="flex-1">
        <h1 class="text-3xl text-center">Find the Landmark</h1>
        <div class="mt-2 mb-2 text-center text-sm text-gray-600">
            {#if taskInProgress}
                Select a spot on the map, then use the sidebar to submit.
            {:else if gameStarted}
                Loading the next task...
            {:else}
                Press "Start Task" to begin.
            {/if}
        </div>
        <div id="map" class="w-full h-[80vh] rounded-lg shadow-xl"></div>
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
