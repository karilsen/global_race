<script>
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";

  let nickname = "";

  async function register() {
      if (!nickname.trim()) {
          alert("Please enter a nickname.");
          return;
      }

      const response = await fetch("http://localhost:5000/register", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ nickname }),
      });

      const result = await response.json();

      if (response.ok) {
          if (typeof window !== "undefined") {
              sessionStorage.setItem("nickname", nickname);
              localStorage.setItem("nickname", nickname); // ✅ Store persistently
          }
          goto("/map");
      } else {
          alert(result.message);
      }
  }

  onMount(() => {
      if (typeof window !== "undefined") {
          const savedNickname = localStorage.getItem("nickname");
          if (savedNickname) {
              sessionStorage.setItem("nickname", savedNickname);
              goto("/map");
          }
      }
  });
</script>

<div class="flex flex-col items-center justify-center min-h-screen">
  <div class="bg-white shadow-lg rounded-lg p-8 w-96">
      <h1 class="text-2xl font-bold text-center mb-4">Register</h1>
      <input 
          type="text" 
          bind:value={nickname} 
          placeholder="Enter your nickname"
          class="w-full px-4 py-2 border border-gray-300 rounded-md mb-4"
      />
      <button 
          on:click={register} 
          class="w-full bg-blue-500 text-white px-4 py-2 rounded-md hover:bg-blue-600 transition"
      >
          Start Game
      </button>
  </div>
</div>
