const FLAGS: Record<string, string> = {
  AR: "\u{1F1E6}\u{1F1F7}",
  UY: "\u{1F1FA}\u{1F1FE}",
  BR: "\u{1F1E7}\u{1F1F7}",
  CL: "\u{1F1E8}\u{1F1F1}",
  CO: "\u{1F1E8}\u{1F1F4}",
  PY: "\u{1F1F5}\u{1F1FE}",
  PE: "\u{1F1F5}\u{1F1EA}",
  VE: "\u{1F1FB}\u{1F1EA}",
  EC: "\u{1F1EA}\u{1F1E8}",
  BO: "\u{1F1E7}\u{1F1F4}",
};

interface CountryFlagProps {
  code?: string | null;
  size?: "sm" | "md" | "lg";
}

export default function CountryFlag({ code, size = "md" }: CountryFlagProps) {
  if (!code) return null;

  const flag = FLAGS[code.toUpperCase()];
  if (!flag) return null;

  const sizeMap = { sm: "1rem", md: "1.25rem", lg: "1.75rem" };

  return (
    <span
      className="country-flag"
      style={{ fontSize: sizeMap[size] }}
      title={code.toUpperCase()}
    >
      {flag}
    </span>
  );
}
