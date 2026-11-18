import { useEffect, useRef, useState } from "react";
import axios from "axios";
import toast, { Toaster } from "react-hot-toast";
import {
  QueryClient,
  QueryClientProvider,
  useMutation,
  useQuery,
} from "@tanstack/react-query";

import signature from "./assets/signature.png";

const API_URL = import.meta.env.VITE_API_URL ?? "http://127.0.0.1:8000";
const ALLOWED = [".mp3", ".wav", ".flac", ".m4a", ".ogg"];
const MAX_MB = 25;

const queryClient = new QueryClient();


/* ---------- API ---------- */

async function uploadSong(file, onProgress) {
  const form = new FormData();
  form.append("file", file);
  const res = await axios.post(`${API_URL}/jobs`, form, {
    onUploadProgress: (e) => {
      if (e.total) onProgress(Math.round((e.loaded / e.total) * 100));
    },
  });
  return res.data;
}

async function fetchJob(jobId) {
  const res = await axios.get(`${API_URL}/jobs/${jobId}`);
  return res.data;
}

function errorMessage(err) {
  if (axios.isAxiosError(err)) {
    if (err.code === "ERR_NETWORK") {
      return "Can't reach the server. Is the backend running?";
    }
    const detail = err.response?.data?.detail;
    if (typeof detail === "string") return detail;
  }
  return "Something went wrong. Please try again.";
}

/* ---------- Shared class names ---------- */

const primaryBtn =
  "mt-5 block w-full cursor-pointer rounded-xl bg-ember py-3.5 text-center text-base font-bold text-white transition hover:bg-ember-deep disabled:cursor-not-allowed disabled:bg-slate-300 disabled:hover:bg-slate-300";
const secondaryBtn =
  "mt-2.5 block w-full cursor-pointer rounded-xl border-2 border-sky-main py-3 font-semibold text-sky-deep transition hover:bg-sky-soft";

/* ---------- Main component ---------- */

const STEPS = ["Queued", "Separating", "Ready"];

function Separator() {
  const [file, setFile] = useState(null);
  const [jobId, setJobId] = useState(null);
  const [dragging, setDragging] = useState(false);
  const [progress, setProgress] = useState(0);
  const inputRef = useRef(null);
  const lastToast = useRef("");

  const upload = useMutation({
    mutationFn: (f) => uploadSong(f, setProgress),
    onSuccess: (job) => {
      setJobId(job.job_id);
      toast.success("Upload complete. Separation started.");
    },
    onError: (err) => toast.error(errorMessage(err)),
  });

  const jobQuery = useQuery({
    queryKey: ["job", jobId],
    queryFn: () => fetchJob(jobId),
    enabled: jobId !== null,
    refetchInterval: (query) => {
      if (query.state.status === "error") return false;
      const state = query.state.data?.state;
      return state === "done" || state === "failed" ? false : 2000;
    },
    retry: (count, err) =>
      !(axios.isAxiosError(err) && err.response?.status === 404) && count < 3,
  });

  const job = jobQuery.data;
  const state = job?.state ?? (jobId ? "queued" : null);

  function reset() {
    setFile(null);
    setJobId(null);
    setProgress(0);
    lastToast.current = "";
    upload.reset();
  }

  // Toast once when a job finishes or fails
  useEffect(() => {
    if (!job || (job.state !== "done" && job.state !== "failed")) return;
    const key = `${job.job_id}:${job.state}`;
    if (lastToast.current === key) return;
    lastToast.current = key;
    if (job.state === "done") toast.success("Your instrumental is ready!");
    else toast.error("Separation failed.");
  }, [job]);

  // If polling fails (for example the server restarted), start over
  useEffect(() => {
    if (!jobQuery.isError) return;
    const notFound =
      axios.isAxiosError(jobQuery.error) &&
      jobQuery.error.response?.status === 404;
    toast.error(
      notFound
        ? "This job was lost (the server may have restarted). Please upload again."
        : errorMessage(jobQuery.error)
    );
    reset();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobQuery.isError]);

  function pickFile(f) {
    if (!f) return;
    const ext = "." + (f.name.split(".").pop() ?? "").toLowerCase();
    if (!ALLOWED.includes(ext)) {
      toast.error(`Unsupported file type. Use ${ALLOWED.join(", ")}`);
      return;
    }
    if (f.size > MAX_MB * 1024 * 1024) {
      toast.error(`File is too large. Maximum is ${MAX_MB} MB.`);
      return;
    }
    setFile(f);
  }

  function onDrop(e) {
    e.preventDefault();
    setDragging(false);
    pickFile(e.dataTransfer.files[0]);
  }

  function startUpload() {
    if (!file) return;
    setProgress(0);
    upload.mutate(file);
  }

  const stepIndex = state === "processing" ? 1 : state === "done" ? 2 : 0;
  const downloadUrl = job ? `${API_URL}/jobs/${job.job_id}/instrumental` : "";

  return (
        <main className="mx-auto w-full max-w-155 flex-1 px-5 py-14">
      <header className="mb-7 text-center">
        <h1 className="text-5xl font-extrabold tracking-tight">
          Voice<span className="text-ember">less</span>
        </h1>
        <p className="mt-2 text-muted">
          Drop in a song and get the instrumental back.
        </p>
      </header>

      <section className="rounded-3xl bg-white p-7 shadow-xl shadow-sky-deep/20">
        {/* 1. Choose a file */}
        {!jobId && !upload.isPending && (
          <>
            <div
              role="button"
              tabIndex={0}
              onClick={() => inputRef.current?.click()}
              onKeyDown={(e) => e.key === "Enter" && inputRef.current?.click()}
              onDragOver={(e) => {
                e.preventDefault();
                setDragging(true);
              }}
              onDragLeave={() => setDragging(false)}
              onDrop={onDrop}
              className={`flex cursor-pointer flex-col items-center gap-1.5 rounded-2xl border-2 border-dashed px-5 py-10 text-center transition ${
                dragging
                  ? "border-sky-deep bg-sky-soft"
                  : "border-sky-main bg-cloud hover:border-sky-deep hover:bg-sky-soft"
              }`}
            >
              <div className="text-4xl text-sky-deep">♪</div>
              <strong>Drag a song here, or click to browse</strong>
              <span className="text-sm text-muted">{ALLOWED.join("  ")}</span>
            </div>
            <input
              ref={inputRef}
              type="file"
              hidden
              accept={ALLOWED.join(",")}
              onChange={(e) => {
                pickFile(e.target.files?.[0]);
                e.target.value = "";
              }}
            />

            {file && (
              <div className="mt-4 flex items-center justify-between gap-3 rounded-xl bg-sky-soft px-4 py-3">
                <div>
                  <div className="break-all font-semibold">{file.name}</div>
                  <div className="text-sm text-muted">
                    {(file.size / 1024 / 1024).toFixed(1)} MB
                  </div>
                </div>
                <button
                  className="cursor-pointer font-semibold text-ember"
                  onClick={() => setFile(null)}
                >
                  Remove
                </button>
              </div>
            )}

            <button className={primaryBtn} disabled={!file} onClick={startUpload}>
              Separate instrumental
            </button>
          </>
        )}

        {/* 2. Uploading */}
        {upload.isPending && (
          <div>
            <h2 className="mb-3.5 text-xl font-bold">Uploading…</h2>
            <div className="h-2.5 overflow-hidden rounded-full bg-sky-soft">
              <div
                className="h-full rounded-full bg-sky-deep transition-[width] duration-200"
                style={{ width: `${progress}%` }}
              />
            </div>
            <p className="mt-3 text-muted">{progress}%</p>
          </div>
        )}

        {/* 3. Processing or done */}
        {jobId && state && state !== "failed" && (
          <div>
            <ol className="mb-5 flex flex-wrap list-none items-center justify-center gap-4 p-0">
              {STEPS.map((label, i) => {
                const finished = i < stepIndex || state === "done";
                const current = i === stepIndex && state !== "done";
                return (
                  <li
                    key={label}
                    className={`flex items-center gap-2 font-semibold ${
                      current ? "text-ink" : "text-muted"
                    }`}
                  >
                    <span
                      className={`grid size-7 place-items-center rounded-full text-xs ${
                        finished
                          ? "bg-sky-main text-white"
                          : current
                            ? "bg-sky-deep text-white"
                            : "bg-sky-soft text-sky-deep"
                      }`}
                    >
                      {finished ? "✓" : i + 1}
                    </span>
                    {label}
                  </li>
                );
              })}
            </ol>

            {state !== "done" && (
              <>
                <div className="h-2.5 overflow-hidden rounded-full bg-sky-soft">
                  <div className="h-full w-[35%] animate-slide rounded-full bg-sky-deep" />
                </div>
                <p className="mt-3 text-muted">
                  {state === "queued"
                    ? "Waiting for its turn…"
                    : "Splitting the vocals from the music. This can take a few minutes, so keep this tab open."}
                </p>
              </>
            )}

            {state === "done" && job && (
              <>
                <h2 className="mb-3.5 text-xl font-bold">
                  Your instrumental is ready
                </h2>
                <audio controls src={downloadUrl} className="w-full" />
                <a className={primaryBtn} href={downloadUrl} download>
                  Download instrumental
                </a>
                <button className={secondaryBtn} onClick={reset}>
                  Separate another song
                </button>
              </>
            )}
          </div>
        )}

        {/* 4. Failed */}
        {state === "failed" && (
          <div>
            <h2 className="mb-3.5 text-xl font-bold text-ember">
              Separation failed
            </h2>
            <p className="text-muted">
              {job?.error ?? "Something went wrong while processing this song."}
            </p>
            <button className={primaryBtn} onClick={reset}>
              Try again
            </button>
          </div>
        )}
      </section>
    </main>
  );
}

function Footer() {
  return (
    <footer className="flex items-center justify-center gap-2 px-5 pb-8 pt-4 text-sm text-muted">
      <span>© 2026</span>
      <img
        src={signature}
        alt="Attah Sunday"
        draggable={false}
        className="h-10 w-auto animate-sign select-none motion-reduce:animate-none"
      />
    </footer>
  );
}

/* ---------- App shell ---------- */

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <div className="flex min-h-screen flex-col bg-linear-to-b from-[#bfe3f7] to-cloud to-60% text-ink">
        <Toaster position="top-center" />
        <Separator />
        <Footer />
      </div>
    </QueryClientProvider>
  );
}