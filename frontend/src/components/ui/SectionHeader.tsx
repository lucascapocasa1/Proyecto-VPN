import { Link } from "react-router-dom";
import type { ReactNode } from "react";

interface SectionHeaderProps {
  title: string;
  linkTo?: string;
  linkText?: string;
  icon?: ReactNode;
}

export default function SectionHeader({ title, linkTo, linkText, icon }: SectionHeaderProps) {
  return (
    <div className="section-header">
      <h2 className={icon ? "has-icon" : undefined}>
        {icon && <span className="section-header-icon">{icon}</span>}
        <span>{title}</span>
      </h2>
      {linkTo && <Link to={linkTo}>{linkText || "Ver todo"}</Link>}
    </div>
  );
}
