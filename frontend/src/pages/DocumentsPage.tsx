import { useState } from "react"
import { FileUp, FileText } from "lucide-react"
import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

export function DocumentsPage() {
  const [dragging, setDragging] = useState(false)

  return (
    <div className="p-8">
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-xl font-semibold text-zinc-100">Documents</h1>
          <p className="text-sm text-zinc-500 mt-1">
            Upload and manage your knowledge base documents.
          </p>
        </div>
        <Button disabled>Upload</Button>
      </div>

      {/* Drop zone */}
      <div
        className={cn(
          "rounded-xl border-2 border-dashed p-16 text-center transition-all",
          dragging
            ? "border-zinc-500 bg-zinc-800/30"
            : "border-zinc-800 bg-zinc-900/30 hover:border-zinc-700"
        )}
        onDragOver={(e) => {
          e.preventDefault()
          setDragging(true)
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault()
          setDragging(false)
        }}
      >
        <div className="flex justify-center mb-4">
          <div className="p-4 rounded-full bg-zinc-800">
            <FileUp className="h-6 w-6 text-zinc-500" />
          </div>
        </div>
        <p className="font-medium text-zinc-300 mb-1">Drag &amp; drop files here</p>
        <p className="text-sm text-zinc-600 mb-5">PDF, DOCX, and Markdown supported</p>
        <Button variant="outline" disabled size="sm">
          Browse files
        </Button>
        <p className="text-xs text-zinc-700 mt-4">Document upload coming soon</p>
      </div>

      {/* Document list */}
      <div className="mt-8">
        <h2 className="text-sm font-medium text-zinc-400 mb-3">Indexed documents</h2>
        <div className="rounded-xl border border-zinc-800 bg-zinc-900/30 py-14 text-center">
          <FileText className="h-6 w-6 mx-auto mb-2 text-zinc-700" />
          <p className="text-sm text-zinc-600">No documents yet</p>
        </div>
      </div>
    </div>
  )
}
