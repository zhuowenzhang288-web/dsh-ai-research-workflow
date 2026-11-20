// Bundled research workflow skill: registers ai-research-workflow SKILL.md on the skill registry.
import { readFile } from 'node:fs/promises'
import { join, sep } from 'node:path'
import { fileURLToPath } from 'node:url'
import { BUNDLED_SKILL_RANK } from '@deepseek-ai/dsh-skill'
import { parse as parseYaml } from 'yaml'

const SKILL_NAME = 'ai-research-workflow'

export const name = 'ai-research-workflow'
export const inject = ['skills']

function parseSkill(raw, path) {
  const frontmatter = /^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/u.exec(raw)
  if (frontmatter?.[1] === undefined) throw new Error(`ai-research-workflow: ${path} has no YAML frontmatter`)
  const metadata = parseYaml(frontmatter[1])
  const description = typeof metadata === 'object' && metadata !== null && 'description' in metadata
    ? metadata.description : undefined
  if (typeof description !== 'string' || description.length === 0) throw new Error(`ai-research-workflow: ${path} has no description`)
  return { description, content: raw.slice(frontmatter[0].length).trim() }
}

export function apply(ctx) {
  const assetRoot = fileURLToPath(new URL('./assets/', import.meta.url))
  const skillPath = join(assetRoot, SKILL_NAME, 'SKILL.md')

  async function readSkill(signal) {
    const raw = await readFile(skillPath, { encoding: 'utf8', signal })
    return parseSkill(raw, skillPath)
  }

  ctx.skills.registerProvider(control => ({
    name: 'dsh-ai-research-workflow',
    async list(options) {
      let read
      try {
        read = await readSkill(options.signal)
      } catch (error) {
        if (options.signal?.aborted === true) throw error
        return { candidates: [], complete: false }
      }
      const directory = join(assetRoot, SKILL_NAME)
      return {
        candidates: [{
          name: SKILL_NAME,
          description: read.description,
          invocation: { modelInvocable: true, userInvocable: true },
          provider: 'dsh-ai-research-workflow',
          source: 'bundled',
          rank: BUNDLED_SKILL_RANK,
          resourceBase: { kind: 'directory', path: directory.split(sep).join('/') },
          locator: skillPath,
        }],
        complete: true,
      }
    },
    async get(candidate, options) {
      const { rank: _rank, locator: _locator, ...summary } = candidate
      const read = await readSkill(options.signal)
      return { ...summary, content: read.content }
    },
  }))
}