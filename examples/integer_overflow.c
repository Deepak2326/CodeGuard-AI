// Held-out Juliet demonstration function; not a complete standalone program.
void example()
{
    char data;
    data = ' ';
    data = CHAR_MAX;
    {
        char result = data + 1;
        printHexCharLine(result);
    }
}
