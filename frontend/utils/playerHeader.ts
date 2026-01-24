export function formatPositions(
  primary: string,
  secondary: string[] = []
): string {
  if (!secondary.length) return primary;

  const visible = secondary.slice(0, 2);
  const rest = secondary.length - visible.length;

  return `${primary} | ${visible.join(", ")}${
    rest > 0 ? ` +${rest}` : ""
  }`;
}

export function getReliability(minutes: number): {
  label: string;
  warning: boolean;
} {
  if (minutes < 300) {
    return {
      label: "Limited data — insights may be unstable",
      warning: true,
    };
  }

  if (minutes < 900) {
    return {
      label: "Medium reliability",
      warning: false,
    };
  }

  return {
    label: "Reliable data",
    warning: false,
  };
}
