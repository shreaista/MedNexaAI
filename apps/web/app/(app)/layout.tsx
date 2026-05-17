import { ShellWrapper } from "@/components/layout/shell-wrapper";

export default function AppSegmentLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return <ShellWrapper>{children}</ShellWrapper>;
}
