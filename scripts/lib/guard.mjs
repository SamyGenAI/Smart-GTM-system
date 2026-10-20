// Paid scripts print an estimate and stop unless --confirm is present.
// --estimate and --dry-run print the same estimate and exit 0.

export function wantsEstimate(argv) {
  return argv.includes("--estimate") || argv.includes("--dry-run");
}

export function hasConfirm(argv) {
  return argv.includes("--confirm");
}

export function gatePaid({ argv, estimate, extra }) {
  const payload = {
    estimate: true,
    confirmed: false,
    paid_calls: false,
    ...estimate,
    ...(extra || {}),
  };
  if (hasConfirm(argv) && !wantsEstimate(argv)) return "confirmed";
  process.stdout.write(`${JSON.stringify(payload, null, 2)}\n`);
  if (wantsEstimate(argv)) return "estimate";
  process.stderr.write(
    "Refusing paid calls without --confirm. Re-run with --estimate to preview, then add --confirm after review.\n",
  );
  return "refused";
}
