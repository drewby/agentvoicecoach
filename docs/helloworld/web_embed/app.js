/**
 * Vocal Bridge — Hello World Agent (Web Embed)
 *
 * Connects to a Vocal Bridge voice agent via LiveKit WebRTC.
 *
 * Flow:
 *   1. User clicks "Start Conversation"
 *   2. Frontend POSTs to /api/session on the backend (server.py)
 *   3. Backend calls Vocal Bridge POST /api/v1/token → returns { livekit_url, token }
 *   4. Frontend connects a LiveKit Room with that token
 *   5. Microphone is published; agent audio is received and played
 *   6. Built-in send_transcript events show live conversation text
 */

(function () {
  "use strict";

  // --- SDK availability check -----------------------------------------------
  if (typeof LivekitClient === "undefined") {
    console.error("[VB] LivekitClient global not found. The livekit-client UMD script may not have loaded.");
    document.getElementById("status").textContent = "Error: LiveKit SDK failed to load.";
    return;
  }
  console.log("[VB] LivekitClient loaded. Keys:", Object.keys(LivekitClient).slice(0, 10).join(", "), "…");
  console.log("[VB] LivekitClient.version:", LivekitClient.version || "(no version property)");

  const { Room, RoomEvent, Track, ConnectionState } = LivekitClient;

  const startBtn = document.getElementById("start-btn");
  const statusEl = document.getElementById("status");
  const vizEl = document.getElementById("visualizer");
  const transcriptEl = document.getElementById("transcript");
  const docPanel = document.getElementById("doc-panel");
  const docContent = document.getElementById("doc-content");
  const copyDocBtn = document.getElementById("copy-doc-btn");
  const dismissDocBtn = document.getElementById("dismiss-doc-btn");
  const topicInput = document.getElementById("topic-input");

  let room = null;

  function setStatus(msg) {
    statusEl.textContent = msg;
  }

  function showVisualizer(visible) {
    vizEl.classList.toggle("visible", visible);
  }

  function appendTranscript(role, text) {
    transcriptEl.classList.add("visible");
    const line = document.createElement("div");
    line.className = role; // "agent" or "user"
    line.textContent = `${role === "agent" ? "Agent" : "You"}: ${text}`;
    transcriptEl.appendChild(line);
    transcriptEl.scrollTop = transcriptEl.scrollHeight;
  }

  function showDocument(text) {
    docContent.textContent = text;
    docPanel.classList.add("visible");
    console.log("[VB] Document received from agent:", text.substring(0, 80), "…");
  }

  // --- Document panel controls ------------------------------------------------

  copyDocBtn.addEventListener("click", () => {
    navigator.clipboard.writeText(docContent.textContent).then(() => {
      copyDocBtn.textContent = "Copied!";
      setTimeout(() => { copyDocBtn.textContent = "Copy"; }, 1500);
    });
  });

  dismissDocBtn.addEventListener("click", () => {
    docPanel.classList.remove("visible");
  });

  // --------------------------------------------------------------------------
  // Backend call — gets a LiveKit token from server.py → Vocal Bridge API
  // --------------------------------------------------------------------------

  async function fetchSession() {
    console.log("[VB] Requesting session token from backend…");
    const resp = await fetch("/api/session", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ participant_name: "Web User" }),
    });

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}));
      console.error("[VB] Backend error:", resp.status, err);
      throw new Error(err.error || `Server returned ${resp.status}`);
    }

    const data = await resp.json();
    console.log("[VB] Session response:", {
      livekit_url: data.livekit_url,
      room_name: data.room_name,
      token: data.token ? data.token.substring(0, 20) + "…" : undefined,
      keys: Object.keys(data),
    });

    if (!data.livekit_url || !data.token) {
      console.error("[VB] Full response:", data);
      throw new Error(
        `Missing fields in response. Got keys: [${Object.keys(data).join(", ")}]. ` +
        "Expected livekit_url and token."
      );
    }

    return data;
  }

  // --------------------------------------------------------------------------
  // LiveKit connection
  // --------------------------------------------------------------------------

  async function connect() {
    setStatus("Requesting session…");
    const data = await fetchSession();
    const livekitUrl = data.livekit_url;
    const token = data.token;

    console.log("[VB] Connecting to LiveKit:", livekitUrl);
    setStatus("Connecting to agent…");
    room = new Room({
      adaptiveStream: true,
      dynacast: true,
    });

    // --- Event handlers -----------------------------------------------------

    room.on(RoomEvent.Connected, () => {
      setStatus("Connected — speak into your microphone");
      showVisualizer(true);
      startBtn.textContent = "End Conversation";
      startBtn.classList.add("active");
      startBtn.disabled = false;
    });

    room.on(RoomEvent.Disconnected, () => {
      setStatus("Disconnected");
      cleanup();
    });

    room.on(RoomEvent.TrackSubscribed, (track, publication, participant) => {
      if (track.kind === Track.Kind.Audio) {
        const el = track.attach();
        el.id = `audio-${participant.identity}`;
        document.body.appendChild(el);
      }
    });

    room.on(RoomEvent.TrackUnsubscribed, (track) => {
      track.detach().forEach((el) => el.remove());
    });

    // Built-in live transcript + client actions from the agent.
    // - send_transcript: automatic transcript events { role, text, timestamp }
    // - send_document: agent sends written content to the screen (not spoken)
    room.on(RoomEvent.DataReceived, (...args) => {
      // Log ALL data channel messages so we can debug payload shape
      const payload = args[0];
      const participant = args[1];
      const kind = args[2];
      const topic = args[3];

      let decoded;
      try {
        decoded = JSON.parse(new TextDecoder().decode(payload));
      } catch {
        return; // not JSON — ignore
      }

      console.log("[VB] DataReceived:", {
        topic,
        kind,
        from: participant?.identity,
        argCount: args.length,
        data: decoded,
      });

      // Try to handle as a client_action regardless of topic,
      // in case the topic arrives differently than expected
      if (decoded.type === "client_action") {
        switch (decoded.action) {
          case "send_transcript": {
            const { role, text } = decoded.payload;
            appendTranscript(role === "user" ? "user" : "agent", text);
            break;
          }
          case "send_document": {
            const text = decoded.payload.markdown
              || decoded.payload.text
              || decoded.payload.content
              || JSON.stringify(decoded.payload, null, 2);
            console.log("[VB] send_document received, showing in UI");
            showDocument(text);
            break;
          }
          case "end_conversation": {
            console.log("[VB] end_conversation received from agent");
            setStatus("Agent ended the conversation.");
            // Short delay so the agent's final words finish playing
            setTimeout(() => cleanup(), 1500);
            break;
          }
          default:
            console.log("[VB] Client action:", decoded.action, decoded.payload);
        }
      }
    });

    room.on(RoomEvent.ConnectionStateChanged, (state) => {
      if (state === ConnectionState.Reconnecting) {
        setStatus("Reconnecting…");
      }
    });

    // --- Connect and publish mic --------------------------------------------

    // Request mic permission first (avoids silent failures)
    await navigator.mediaDevices.getUserMedia({ audio: true });
    console.log("[VB] Microphone permission granted");

    console.log("[VB] room.connect() args:", {
      url: livekitUrl,
      urlType: typeof livekitUrl,
      tokenPrefix: token ? token.substring(0, 20) : token,
      tokenType: typeof token,
    });

    if (typeof livekitUrl !== "string" || !livekitUrl.startsWith("wss://")) {
      throw new Error(
        `Invalid livekit_url: "${livekitUrl}". Expected a wss:// URL. ` +
        "Check the server.py terminal logs for the API response."
      );
    }

    await room.connect(livekitUrl, token);
    console.log("[VB] Connected to room:", room.name);
    await room.localParticipant.setMicrophoneEnabled(true);
    console.log("[VB] Microphone enabled — speak now");

    // Send initial topic/context if the user provided one
    const topic = topicInput.value.trim();
    if (topic) {
      const payload = JSON.stringify({
        type: "client_action",
        action: "session_context",
        payload: { text: topic },
      });
      const encoded = new TextEncoder().encode(payload);
      await room.localParticipant.publishData(encoded, { topic: "client_actions" });
      console.log("[VB] Sent session_context:", topic);
      topicInput.disabled = true;
    }
  }

  function cleanup() {
    showVisualizer(false);
    startBtn.textContent = "Start Conversation";
    startBtn.classList.remove("active");
    startBtn.disabled = false;
    topicInput.disabled = false;
    if (room) {
      room.disconnect();
      room = null;
    }
  }

  // --------------------------------------------------------------------------
  // Button handler — toggle start / stop
  // --------------------------------------------------------------------------

  startBtn.addEventListener("click", async () => {
    if (room) {
      cleanup();
      setStatus("Conversation ended.");
      return;
    }

    startBtn.disabled = true;
    setStatus("");
    transcriptEl.innerHTML = "";
    transcriptEl.classList.remove("visible");
    docPanel.classList.remove("visible");

    try {
      await connect();
    } catch (err) {
      console.error("Connection failed:", err);
      setStatus("Error: " + err.message);
      cleanup();
    }
  });
})();
