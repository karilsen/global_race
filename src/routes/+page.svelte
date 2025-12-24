<script>
    import { onMount } from "svelte";
    import { goto } from "$app/navigation";

    let nickname = "";
    let error = "";
    let loading = false;

    onMount(() => {
        if (typeof window !== "undefined") {
            const saved = localStorage.getItem("nickname") || sessionStorage.getItem("nickname");
            if (saved) {
                goto("/map");
            }
        }
    });

    async function startGame() {
        error = "";
        if (!nickname.trim()) {
            error = "Please enter a nickname.";
            return;
        }
        loading = true;
        try {
            const res = await fetch("http://localhost:5000/register", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ nickname }),
            });
            const data = await res.json();
            if (!res.ok) {
                error = data.message || "Could not register. Try another nickname.";
                return;
            }
            if (typeof window !== "undefined") {
                sessionStorage.setItem("nickname", nickname);
                localStorage.setItem("nickname", nickname);
            }
            goto("/map");
        } catch (e) {
            error = "Network error. Please try again.";
        } finally {
            loading = false;
        }
    }
</script>

<div class="flex items-center justify-center min-h-screen bg-gray-100">
    <div class="bg-white shadow-lg rounded-lg p-8 w-full max-w-md">
        <h1 class="text-3xl font-bold text-center text-blue-600">Global Race</h1>
        <p class="text-center text-gray-600 mt-2">Pick a nickname to jump into the game.</p>

        <label class="block mt-6 text-sm text-gray-700">Nickname</label>
        <input
            class="w-full mt-1 px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-400"
            type="text"
            bind:value={nickname}
            placeholder="e.g. MapMaster"
            on:keydown={(e) => e.key === 'Enter' && startGame()}
        />

        {#if error}
            <p class="mt-3 text-sm text-red-600">{error}</p>
        {/if}

        <button
            class="mt-6 w-full bg-blue-500 text-white py-2 rounded-md hover:bg-blue-600 disabled:opacity-60"
            on:click={startGame}
            disabled={loading}
        >
            {loading ? "Starting..." : "Start Playing"}
        </button>
    </div>
</div>
