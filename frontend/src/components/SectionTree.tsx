import type { DocumentationTreeNode } from "../api/types";

interface SectionTreeProps {
  roots: DocumentationTreeNode[];
  selectedPath?: string;
  onSelect: (path: string) => void;
}

interface TreeNodeProps {
  node: DocumentationTreeNode;
  selectedPath?: string;
  onSelect: (path: string) => void;
}

function TreeNode({ node, selectedPath, onSelect }: TreeNodeProps) {
  const isSelected = selectedPath === node.path;

  return (
    <li>
      <button
        type="button"
        className={isSelected ? "selected" : ""}
        onClick={() => onSelect(node.path)}
      >
        {node.title ?? node.path}
      </button>
      {node.children.length ? (
        <ul>
          {node.children.map((child) => (
            <TreeNode key={child.id} node={child} selectedPath={selectedPath} onSelect={onSelect} />
          ))}
        </ul>
      ) : null}
    </li>
  );
}

export function SectionTree({ roots, selectedPath, onSelect }: SectionTreeProps) {
  if (!roots.length) {
    return <p>No sections available.</p>;
  }

  return (
    <ul className="section-tree" aria-label="Documentation section tree">
      {roots.map((root) => (
        <TreeNode key={root.id} node={root} selectedPath={selectedPath} onSelect={onSelect} />
      ))}
    </ul>
  );
}
