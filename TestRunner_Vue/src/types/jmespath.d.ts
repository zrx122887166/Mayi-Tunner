declare module 'jmespath' {
  export function search(data: any, expression: string): any;
  export function compile(expression: string): (data: any) => any;
}