import { Link } from "react-router-dom";

interface SectionHeaderProps {
  title: string;
  linkTo?: string;
  linkText?: string;
}

export default function SectionHeader({ title, linkTo, linkText }: SectionHeaderProps) {
  return (
    <div className="section-header">
      <h2>{title}</h2>
      {linkTo && <Link to={linkTo}>{linkText || "Ver todo"}</Link>}
    </div>
  );
}
