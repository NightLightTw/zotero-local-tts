/* global Components, IOUtils, PathUtils, Services, Zotero */

"use strict";

const PLUGIN_NAME = "Zotero Local TTS";
const SUPPORTED_VERSION = /^9\.0\./;
const BRIDGE_URL = "http://127.0.0.1:8766";
const MODEL = "qwen3-customvoice-1.7b-8bit";
const LOCAL_VOICES = {
  "zotero-local-qwen-aiden": {
    engineVoice: "Aiden",
    label: "Aiden (Qwen3-TTS, Local)",
    sample: "This is Aiden, reading locally with Qwen three text to speech.",
  },
  "zotero-local-qwen-ryan": {
    engineVoice: "Ryan",
    label: "Ryan (Qwen3-TTS, Local)",
    sample: "This is Ryan, reading locally with Qwen three text to speech.",
  },
  "zotero-local-qwen-vivian": {
    engineVoice: "Vivian",
    label: "Vivian (Qwen3-TTS, Local)",
    sample: "这是 Vivian，正在使用 Qwen 三文字转语音进行本地朗读。",
  },
  "zotero-local-qwen-serena": {
    engineVoice: "Serena",
    label: "Serena (Qwen3-TTS, Local)",
    sample: "这是 Serena，正在使用 Qwen 三文字转语音进行本地朗读。",
  },
  "zotero-local-qwen-uncle-fu": {
    engineVoice: "Uncle_Fu",
    label: "Uncle Fu (Qwen3-TTS, Local)",
    sample: "这是 Uncle Fu，正在使用 Qwen 三文字转语音进行本地朗读。",
  },
  "zotero-local-qwen-dylan": {
    engineVoice: "Dylan",
    label: "Dylan (Qwen3-TTS, Local)",
    sample: "这是 Dylan，正在使用 Qwen 三文字转语音进行本地朗读。",
  },
  "zotero-local-qwen-eric": {
    engineVoice: "Eric",
    label: "Eric (Qwen3-TTS, Local)",
    sample: "这是 Eric，正在使用 Qwen 三文字转语音进行本地朗读。",
  },
  "zotero-local-qwen-ono-anna": {
    engineVoice: "Ono_Anna",
    label: "Ono Anna (Qwen3-TTS, Local)",
    sample: "小野アンナです。Qwen三の音声合成でローカルに読み上げています。",
  },
  "zotero-local-qwen-sohee": {
    engineVoice: "Sohee",
    label: "Sohee (Qwen3-TTS, Local)",
    sample: "소희입니다. Qwen 삼 음성 합성으로 로컬에서 읽고 있습니다.",
  },
};

let originalGetReadAloudVoices;
let originalGetReadAloudAudio;
let patchedGetReadAloudVoices;
let patchedGetReadAloudAudio;
let lastLocalFailureNotice = 0;

const LOCAL_FAILURE_NOTICE_INTERVAL_MS = 30_000;

function log(message) {
  Zotero.debug(`${PLUGIN_NAME}: ${message}`);
}

function tokenPath() {
  const home = Services.dirsvc.get("Home", Components.interfaces.nsIFile).path;
  return PathUtils.join(
    home,
    "Library",
    "Application Support",
    "Zotero Local TTS",
    "token"
  );
}

async function readToken() {
  const token = (await IOUtils.readUTF8(tokenPath())).trim();
  if (!token) {
    throw new Error("The local bridge token file is empty");
  }
  return token;
}

function localFailureMessage(error) {
  const status = Number(error?.status || error?.xmlhttp?.status || 0);
  if (error?.localTTSFailure === "token" || status === 401) {
    return "The local TTS bridge rejected Zotero's token. Reinstall or restart the background service.";
  }
  if (status === 503) {
    return "The local TTS model could not synthesize this text. Check bridge-error.log for the safe failure category.";
  }
  return "Zotero could not reach the local TTS bridge at 127.0.0.1:8766. Start or reinstall the background service, then choose Retry. Internet access is not required.";
}

function reportLocalFailure(error) {
  const status = Number(error?.status || error?.xmlhttp?.status || 0);
  log(
    `local synthesis failed (${error?.name || "Error"}, status=${status || "unavailable"})`
  );

  const now = Date.now();
  if (now - lastLocalFailureNotice < LOCAL_FAILURE_NOTICE_INTERVAL_MS) {
    return;
  }
  lastLocalFailureNotice = now;
  try {
    Services.prompt.alert(null, PLUGIN_NAME, localFailureMessage(error));
  } catch (noticeError) {
    log(`could not display local failure details (${noticeError?.name || "Error"})`);
  }
}

function localVoiceResponse() {
  const voiceLabels = Object.fromEntries(
    Object.entries(LOCAL_VOICES).map(([id, voice]) => [id, { label: voice.label }])
  );
  return {
    voices: {
      standard: [
        {
          creditsPerMinute: 0,
          segmentGranularity: "sentence",
          sentenceDelay: 0,
          locales: {
            "en-US": {
              default: ["zotero-local-qwen-aiden"],
              other: ["zotero-local-qwen-ryan"],
            },
            "zh-CN": {
              default: ["zotero-local-qwen-vivian"],
              other: [
                "zotero-local-qwen-serena",
                "zotero-local-qwen-uncle-fu",
                "zotero-local-qwen-dylan",
                "zotero-local-qwen-eric",
              ],
            },
            "ja-JP": {
              default: ["zotero-local-qwen-ono-anna"],
              other: [],
            },
            "ko-KR": {
              default: ["zotero-local-qwen-sohee"],
              other: [],
            },
          },
          voices: voiceLabels,
        },
      ],
    },
    standardCreditsRemaining: null,
    premiumCreditsRemaining: null,
    devMode: false,
  };
}

async function mergedVoiceResponse(apiClient) {
  const local = localVoiceResponse();
  try {
    const original = await originalGetReadAloudVoices.call(apiClient);
    if (original?.error || !original?.voices) {
      return local;
    }
    const originalStandard = Array.isArray(original.voices.standard)
      ? original.voices.standard
      : [];
    return {
      ...original,
      voices: {
        ...original.voices,
        standard: [...local.voices.standard, ...originalStandard],
      },
    };
  } catch (error) {
    log(`original voice listing failed (${error?.name || "Error"})`);
    return local;
  }
}

async function requestAudio(segment, voiceID) {
  const localVoice = Object.prototype.hasOwnProperty.call(LOCAL_VOICES, voiceID)
    ? LOCAL_VOICES[voiceID]
    : null;
  if (!localVoice) {
    return originalGetReadAloudAudio.call(this, segment, voiceID);
  }

  const input = segment === "sample" ? localVoice.sample : segment?.text;
  if (!input || typeof input !== "string") {
    return { error: "unknown" };
  }

  try {
    let token;
    try {
      token = await readToken();
    } catch (tokenError) {
      const wrappedError = new Error("The local bridge token could not be read", {
        cause: tokenError,
      });
      wrappedError.localTTSFailure = "token";
      throw wrappedError;
    }
    const xmlhttp = await Zotero.HTTP.request(
      "POST",
      `${BRIDGE_URL}/v1/audio/speech`,
      {
        headers: {
          Authorization: `Bearer ${token}`,
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          model: MODEL,
          voice: localVoice.engineVoice,
          input,
          response_format: "wav",
          speed: 1.0,
        }),
        responseType: "blob",
        successCodes: [200],
        errorDelayMax: 1000,
      }
    );
    return { audio: xmlhttp.response };
  } catch (error) {
    // Never log the request text or bearer token.
    reportLocalFailure(error);
    // Zotero 9 only defines network, quota, and unknown Read Aloud errors.
    // "unknown" avoids falsely instructing an offline user to check the internet.
    return { error: "unknown" };
  }
}

async function startup() {
  await Zotero.initializationPromise;

  if (!SUPPORTED_VERSION.test(Zotero.version)) {
    throw new Error(`${PLUGIN_NAME} does not support Zotero ${Zotero.version}`);
  }

  const prototype = Zotero.Sync?.APIClient?.prototype;
  if (
    !prototype ||
    typeof prototype.getReadAloudVoices !== "function" ||
    typeof prototype.getReadAloudAudio !== "function"
  ) {
    throw new Error(`${PLUGIN_NAME}: expected Read Aloud API contract is missing`);
  }

  originalGetReadAloudVoices = prototype.getReadAloudVoices;
  originalGetReadAloudAudio = prototype.getReadAloudAudio;
  patchedGetReadAloudVoices = async function () {
    return mergedVoiceResponse(this);
  };
  patchedGetReadAloudAudio = requestAudio;

  prototype.getReadAloudVoices = patchedGetReadAloudVoices;
  prototype.getReadAloudAudio = patchedGetReadAloudAudio;
  log(`enabled for Zotero ${Zotero.version}`);
}

function shutdown() {
  const prototype = Zotero.Sync?.APIClient?.prototype;
  if (!prototype) {
    return;
  }
  if (prototype.getReadAloudVoices === patchedGetReadAloudVoices) {
    prototype.getReadAloudVoices = originalGetReadAloudVoices;
  }
  if (prototype.getReadAloudAudio === patchedGetReadAloudAudio) {
    prototype.getReadAloudAudio = originalGetReadAloudAudio;
  }
  log("disabled and restored Zotero methods");
}

function install() {}

function uninstall() {}
