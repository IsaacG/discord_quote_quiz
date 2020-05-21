#!/bin/python

import collections
import more_itertools
import os
import random
import string
from dataclasses import dataclass
from discord.ext import commands


QUOTES = 'quotes.txt'

def SuperStrip(s):
  return ''.join(l for l in s.lower() if l in string.ascii_letters + string.digits)


@dataclass
class Quote:
  quote: str
  movie: str

  def __post_init__(self):
    self.quote = self.quote.strip()
    self.movie = self.movie.strip()

  def __str__(self):
    return '%s\n%s\n' % (self.quote, self.movie)


class Quotes:

  def __init__(self, filename: str):
    self._filename = filename
    self.quotes = []
    self.LoadQuotes()

  def LoadQuotes(self):
    self.cache = []
    with open(self._filename) as f:
      for i, lines in enumerate(more_itertools.chunked(f.readlines(), 2)):
        self.cache.append(Quote(quote=lines[0], movie=lines[1]))
        
  def GetQuote(self):
    if not self.quotes:
      self.quotes = list(self.cache)
      random.shuffle(self.quotes)
    return self.quotes.pop()

  def AddQuote(self, quote, movie):
    self.cache.append(Quote(quote=quote, movie=movie))
    self.Persist()
    
  def DelQuote(self, quote):
    self.cache.remove(quote)
    self.Persist()

  def Persist(self):
    with open(self._filename, 'wt') as f:
      for q in self.cache:
        f.write(str(q))
    

class QuoteQuiz(commands.Cog):
  """Try to guess where a quote is from."""

  qualified_name = 'Quote Quiz'
  PROMPT = 'What movie is this quote from? %s'

  def __init__(self, filename=QUOTES):
    super()
    self.quotes = Quotes(filename)
    self.current = None
    self.guesses = 0
    self.adding = collections.defaultdict(dict)

  @commands.command()
  async def quote(self, ctx):
    if self.current is not None and self.guesses < 3:
      await ctx.send('Try a few more guesses first!')
      return

    if self.current is not None:
      await ctx.send('%s --%s' % (self.current.quote, self.current.movie))
      
    await self.NextQuote(ctx)

  async def NextQuote(self, ctx):
    self.current = self.quotes.GetQuote()
    self.guesses = 0
    await ctx.send(self.PROMPT % self.current.quote)

  @commands.command()
  async def guess(self, ctx):
    if self.current is None:
      return
    self.guesses += 1
    title = self.CommandContent(ctx)
    if SuperStrip(title) == SuperStrip(self.current.movie):
      await ctx.send('%s got it! The movie is: %s' % (ctx.author.display_name, self.current.movie))
      await self.NextQuote(ctx)
    else:
      await ctx.send('%s, that is not it.' % ctx.author.display_name)

  def CommandContent(self, ctx):
    return ctx.message.content[len(ctx.invoked_with) + 2:]

  async def MaybeAddNew(self, ctx):
    entry = self.adding[ctx.author]
    if 'quote' in entry and 'movie' in entry:
      self.quotes.AddQuote(entry['quote'], entry['movie'])
      del self.adding[ctx.author]
      await ctx.send('%s added a new quote!' % ctx.author.display_name)
    elif 'quote' in entry and 'movie' not in entry:
      await ctx.send('Now tell me what movie that was from, %s, with !addmovie The Movie Title' % ctx.author.display_name)
    elif 'quote' not in entry and 'movie' in entry:
      await ctx.send('Now tell me the quote from that movie, %s, with !addquote The Best Quote Ever' % ctx.author.display_name)

  @commands.command()
  async def delquote(self, ctx):
    if self.current is None:
      return
    self.quotes.DelQuote(self.current)
    await ctx.send('Deleted the last quote')

  @commands.command()
  async def addquote(self, ctx):
    self.adding[ctx.author]['quote'] = self.CommandContent(ctx)
    await self.MaybeAddNew(ctx)

  @commands.command()
  async def addmovie(self, ctx):
    self.adding[ctx.author]['movie'] = self.CommandContent(ctx)
    await self.MaybeAddNew(ctx)


def main():
  token = os.getenv('DISCORD_TOKEN')
  if token is None:
    raise Exception('Token not found')
  bot = commands.Bot(command_prefix='!')
  bot.add_cog(QuoteQuiz())
  bot.run(os.getenv('DISCORD_TOKEN'))


if __name__ == '__main__':
  main()

# vim:ts=2:sw=2:expandtab
