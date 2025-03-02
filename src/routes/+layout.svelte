<script>
	import "../app.css"
    import { onMount } from "svelte";
    import { goto } from "$app/navigation";

    onMount(() => {
        if (typeof window !== "undefined") {
            let storedNickname = sessionStorage.getItem("nickname") || localStorage.getItem("nickname");
            if (!storedNickname) {
                goto("/register");
            } else {
                sessionStorage.setItem("nickname", storedNickname);
            }
        }
    });
</script>

<slot />
