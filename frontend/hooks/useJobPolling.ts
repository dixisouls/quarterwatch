import { useState, useEffect, useRef, useCallback } from "react";
import { useRouter } from "next/router";
import { getJobStatus } from "@/lib/api";
import type { JobStatus, JobStatusResponse } from "@/types";

const POLL_INTERVAL_MS = 3000;
const TERMINAL_STATUSES: JobStatus[] = ["complete", "failed", "awaiting_upload"];

interface UseJobPollingResult {
  status: JobStatus | null;
  jobData: JobStatusResponse | null;
  isPolling: boolean;
  error: string | null;
  stopPolling: () => void;
}

export function useJobPolling(jobId: string | null): UseJobPollingResult {
  const router = useRouter();
  const [status, setStatus] = useState<JobStatus | null>(null);
  const [jobData, setJobData] = useState<JobStatusResponse | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const isMountedRef = useRef(true);

  const stopPolling = useCallback(() => {
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
    setIsPolling(false);
  }, []);

  const poll = useCallback(async () => {
    if (!jobId) return;
    try {
      const data = await getJobStatus(jobId);
      if (!isMountedRef.current) return;

      setJobData(data);
      setStatus(data.status);

      if (TERMINAL_STATUSES.includes(data.status)) {
        stopPolling();
        if (data.status === "complete") {
          router.push(`/results/${jobId}`);
        }
      }
    } catch (err) {
      if (!isMountedRef.current) return;
      setError("Lost connection to the server. Retrying...");
    }
  }, [jobId, router, stopPolling]);

  useEffect(() => {
    isMountedRef.current = true;
    if (!jobId) return;

    setIsPolling(true);
    setError(null);
    poll();

    intervalRef.current = setInterval(poll, POLL_INTERVAL_MS);

    return () => {
      isMountedRef.current = false;
      stopPolling();
    };
  }, [jobId, poll, stopPolling]);

  return { status, jobData, isPolling, error, stopPolling };
}
